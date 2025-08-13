from Chest_Xray_Report.constants import *
from Chest_Xray_Report.entity.config_entity import DataIngestionConfig
from Chest_Xray_Report.utils.common import read_yaml,create_directories

class ConfigurationManager:
    def __init__(
            self,
            config_file_path = CONFIG_FILE_PATH,
            parms_file_path = PARAMS_FILE_PATH     
            ):
        self.config = read_yaml(config_file_path)
        self.parms =  read_yaml(parms_file_path)

        create_directories([self.config.artifacts_root])

    
    def get_data_ingestion_config(self) ->DataIngestionConfig:
        config = self.config.data_ingestion

        create_directories([config.root_dir])
        data_ingestion_config = DataIngestionConfig(
            root_dir=config.root_dir,
            image_URL=config.image_URL,
            report_URL=config.report_URL,
            image_data_file=config.image_data_file,
            report_data_file=config.report_data_file,
            unzip_dir_image = config.unzip_dir_image,
            unzip_dir_report = config.unzip_dir_report,
            all_csv_path = config.all_csv_path,
            train_csv_path = config.train_csv_path,
            test_csv_path = config.test_csv_path
        )

        return data_ingestion_config