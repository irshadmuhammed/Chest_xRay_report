import random
import re

import pandas as pd
from Chest_Xray_Report.entity.config_entity import DataIngestionConfig
from Chest_Xray_Report.utils.common import download_file, extract_tgz
import os
from Chest_Xray_Report import logger
import xml.etree.ElementTree as ET


class DataIngestion:
    def __init__(self,config:DataIngestionConfig):
        self.config = config

    def start_download_extract(self):
        try:
            data_image_url = self.config.image_URL
            data_report_url = self.config.report_URL
            image_dir_down = self.config.image_data_file
            report_dir_down = self.config.report_data_file
            unzip_dir_image = self.config.unzip_dir_image
            unzip_dir_reports = self.config.unzip_dir_report
            

            os.makedirs("artifacts/data_ingestion", exist_ok=True)
            os.makedirs("artifacts/data_ingestion/image", exist_ok=True)
            os.makedirs("artifacts/data_ingestion/report", exist_ok=True)

            logger.info("downloading the data")

            image_dir_down = download_file(data_image_url,image_dir_down)
            report_dir_down = download_file(data_report_url,report_dir_down)

            extract_tgz(image_dir_down, unzip_dir_image)
            extract_tgz(report_dir_down, unzip_dir_reports)

            
        except Exception as e:
            raise e

    def remove_folder(self):
        ecgen_path = os.path.join(self.config.unzip_dir_report, "ecgen-radiology")
        if os.path.exists(ecgen_path):
            for file in os.listdir(ecgen_path):
                if file.endswith(".xml"):
                    os.rename(os.path.join(ecgen_path, file), os.path.join(self.config.unzip_dir_report, file))
            os.rmdir(ecgen_path)

    
    
    def convert_to_csv(self):
        all_data_csv = self.config.all_csv_path
        test_data_csv = self.config.test_csv_path
        train_data_csv = self.config.train_csv_path
        # Ensure report folder exists
        if not os.path.exists(self.config.unzip_dir_report):
            raise FileNotFoundError(f"Report folder not found: {self.config.unzip_dir_report}")

        reports = os.listdir(self.config.unzip_dir_report)
        reports.sort()

        reports_with_no_image = []
        reports_with_empty_sections = []
        reports_with_no_impression = []
        reports_with_no_findings = []

        images_captions = {}
        reports_with_images = {}
        text_of_reports = {}

        def get_new_csv_dictionary():
            return {
                'Image Index': [],
                'Patient ID': [],
                'Findings': [],
                'Impression': [],
                'Caption': [],
                'Manual Tags': []
            }

        all_data_csv_dictionary = get_new_csv_dictionary()
        patient_id = 0
        manual_tags_dic = {}
        manual_tags_list = []

        # === Step 1: Parse reports ===
        for report in reports:
            report_path = os.path.join(self.config.unzip_dir_report, report)
            if not os.path.isfile(report_path):
                continue  # skip folders

            try:
                tree = ET.parse(report_path)
                root = tree.getroot()
            except ET.ParseError:
                print(f"Skipping invalid XML: {report}")
                continue

            img_ids = []
            impression = None
            findings = None

            # Find images
            images = root.findall("parentImage")
            if len(images) == 0:
                reports_with_no_image.append(report)
                continue

            # Extract sections
            sections = root.find("MedlineCitation").find("Article").find("Abstract").findall("AbstractText")
            for section in sections:
                label = section.get("Label")
                if label == "FINDINGS":
                    findings = section.text
                elif label == "IMPRESSION":
                    impression = section.text

            if impression is None and findings is None:
                reports_with_empty_sections.append(report)
                continue

            if impression is None:
                reports_with_no_impression.append(report)
                caption = findings or ""
            elif findings is None:
                reports_with_no_findings.append(report)
                caption = impression or ""
            else:
                caption = f"\"{impression}\n{findings}\""

            # Manual tags
            manual_tags = root.find("MeSH").findall("major")
            manual_tags_tmp = []
            for manual_tag in manual_tags:
                manual_tag = manual_tag.text.lower().strip()
                manual_tag_parts = re.split('/|,', manual_tag)
                for word in manual_tag_parts:
                    word = word.strip()
                    manual_tags_dic[word] = manual_tags_dic.get(word, 0) + 1
                    manual_tags_tmp.append(word)

            # Append data for each image
            for image in images:
                manual_tags_list.append(manual_tags_tmp)

                image_name = f"{image.get('id')}.png"
                images_captions[image_name] = caption
                img_ids.append(image_name)

                all_data_csv_dictionary['Image Index'].append(image_name)
                all_data_csv_dictionary['Patient ID'].append(patient_id)
                all_data_csv_dictionary['Findings'].append('startseq ' + (findings or '') + ' endseq')
                all_data_csv_dictionary['Impression'].append('startseq ' + (impression or '') + ' endseq')
                all_data_csv_dictionary['Caption'].append('startseq ' + caption + ' endseq')

            reports_with_images[report] = img_ids
            text_of_reports[report] = caption
            patient_id += 1

        # === Step 2: Process manual tags ===
        appearance_limit = 25
        to_ignore = []
        selected_classes = {}
        for tags_list in manual_tags_list:
            tags_str = ''
            tags_list = list(set(tags_list))
            for tag in tags_list:
                if manual_tags_dic[tag] > appearance_limit and tag not in to_ignore:
                    selected_classes[tag] = manual_tags_dic[tag]
                    tags_str = f"{tags_str},{tag}" if tags_str else tag
            if tags_str == '':
                tags_str = 'normal'
            all_data_csv_dictionary['Manual Tags'].append(tags_str)

        print("Selected classes:", list(selected_classes.keys()))


        logger.info("Train test split")
        # === Step 3: Split into train/test sets ===
        def append_to_csv_dic(csv_dictionary, index):
            for key in csv_dictionary.keys():
                csv_dictionary[key].append(all_data_csv_dictionary[key][index])

        random.seed(42)  # reproducibility
        num_of_images = len(all_data_csv_dictionary['Image Index'])
        test_ratio = 0.2  # or keep fixed number if you prefer
        num_test_images = int(num_of_images * test_ratio)

        test_indices = set(random.sample(range(num_of_images), num_test_images))

        test_csv_dictionary = get_new_csv_dictionary()
        train_csv_dictionary = get_new_csv_dictionary()

        for i in range(num_of_images):
            if i in test_indices:
                append_to_csv_dic(test_csv_dictionary, i)
            else:
                append_to_csv_dic(train_csv_dictionary, i)

        # === Step 4: Save CSV files ===

        def save_csv(csv_dictionary, csv_name, just_caption=False):
            if just_caption:
                df = pd.DataFrame({'Caption': csv_dictionary['Caption']})
                df.to_csv(csv_name, index=False, header=False)
            else:
                df = pd.DataFrame(csv_dictionary)
                df.to_csv(csv_name, index=False)

        logger.info("Saving the csv")
        save_csv(all_data_csv_dictionary, all_data_csv)
        save_csv(train_csv_dictionary, train_data_csv)
        save_csv(test_csv_dictionary, test_data_csv)

        print("Train size:", len(train_csv_dictionary['Image Index']))
        print("Test size:", len(test_csv_dictionary['Image Index']))

        