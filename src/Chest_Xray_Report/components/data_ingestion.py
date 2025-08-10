from Chest_Xray_Report.entity.config_entity import DataIngestionConfig
from Chest_Xray_Report.utils.common import download_file, extract_tgz
import os
from Chest_Xray_Report import logger


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