from Chest_Xray_Report import logger
from Chest_Xray_Report.pipeline.stage_01_data_ingestion import DataIngestionTrainingPipeline

STAGE_NAME = "Data ingestion stage"

try:
    logger.info(f"----------stage{STAGE_NAME} started-----")
    obj = DataIngestionTrainingPipeline()
    obj.main()
    logger.info(f"----------stage{STAGE_NAME} completed-----")
except Exception as e:
    raise e