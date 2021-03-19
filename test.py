# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import crawler_dag_builder

if __name__ == "__main__":
    project_path = os.getcwd()[:os.getcwd().rfind(os.sep)]
    os.putenv('AIRFLOW__KUBERNETES__GIT_DAGS_FOLDER_MOUNT_POINT', project_path)
    os.putenv('AIRFLOW__KUBERNETES__GIT_DAGS_VOLUME_SUBPATH', 'airflow')
    builder = crawler_dag_builder.CrawlerDagBuilder()
    config = builder.open_config(f"news{os.sep}cctoday_job.yaml")
    print(config)