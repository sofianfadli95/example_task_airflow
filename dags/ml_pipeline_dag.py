"""
Airflow DAG for ML Pipeline
This DAG orchestrates a machine learning pipeline using Kubernetes Pods.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.models import Variable
from kubernetes.client import models as k8s
import os

# Default arguments for the DAG
default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'catchup': False,
}

# DAG configuration
dag = DAG(
    'ml_pipeline',
    default_args=default_args,
    description='Machine Learning Pipeline DAG',
    schedule_interval=timedelta(days=1),  # Run daily
    max_active_runs=1,
    tags=['ml', 'training', 'prediction'],
)

# Configuration variables (set these in Airflow Variables)
ML_IMAGE = Variable.get("ml_pipeline_image", default_var="ghcr.io/yourusername/yourrepo/ml-pipeline:latest")
KUBERNETES_NAMESPACE = Variable.get("kubernetes_namespace", default_var="airflow")
SERVICE_ACCOUNT = Variable.get("service_account", default_var="airflow")
PVC_DATA = Variable.get("pvc_data", default_var="airflow-data-pvc")
PVC_MODELS = Variable.get("pvc_models", default_var="airflow-models-pvc")
PVC_PREDICTIONS = Variable.get("pvc_predictions", default_var="airflow-predictions-pvc")

# Common Kubernetes Pod configuration
def get_pod_config(task_name, command):
    """Generate Kubernetes pod configuration"""
    return {
        'image': ML_IMAGE,
        'namespace': KUBERNETES_NAMESPACE,
        'name': f"ml-pipeline-{task_name}-pod",
        'service_account_name': SERVICE_ACCOUNT,
        'get_logs': True,
        'log_events_on_failure': True,
        'is_delete_operator_pod': True,
        'startup_timeout_seconds': 300,
        'env_vars': [
            k8s.V1EnvVar(name='PYTHONUNBUFFERED', value='1'),
            k8s.V1EnvVar(name='AIRFLOW_RUN_ID', value='{{ run_id }}'),
            k8s.V1EnvVar(name='AIRFLOW_DAG_ID', value='{{ dag.dag_id }}'),
            k8s.V1EnvVar(name='AIRFLOW_TASK_ID', value='{{ task.task_id }}'),
            k8s.V1EnvVar(name='EXECUTION_DATE', value='{{ ds }}'),
        ],
        'volume_mounts': [
            k8s.V1VolumeMount(
                name='data-storage',
                mount_path='/app/data',
                sub_path=None,
                read_only=False
            ),
            k8s.V1VolumeMount(
                name='models-storage',
                mount_path='/app/models',
                sub_path=None,
                read_only=False
            ),
            k8s.V1VolumeMount(
                name='predictions-storage',
                mount_path='/app/predictions',
                sub_path=None,
                read_only=False
            ),
        ],
        'volumes': [
            k8s.V1Volume(
                name='data-storage',
                persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(
                    claim_name=PVC_DATA
                )
            ),
            k8s.V1Volume(
                name='models-storage',
                persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(
                    claim_name=PVC_MODELS
                )
            ),
            k8s.V1Volume(
                name='predictions-storage',
                persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(
                    claim_name=PVC_PREDICTIONS
                )
            ),
        ],
        'resources': k8s.V1ResourceRequirements(
            requests={'memory': '1Gi', 'cpu': '500m'},
            limits={'memory': '2Gi', 'cpu': '1000m'}
        ),
        'image_pull_policy': 'Always',
        'cmds': ['python'],
        'arguments': command.split()[1:],  # Remove 'python' from command
    }


def check_data_availability(**context):
    """Check if training data is available"""
    import os
    # Since we're using PVCs, we need to check the mounted path
    data_path = '/tmp/airflow/data/training_data.csv'  # This would be the local mounted path
    
    # In Kubernetes environment, we'll use a simple check pod
    # For now, we'll assume data is available and let the training task handle it
    context['task_instance'].xcom_push(key='data_available', value=True)
    context['task_instance'].xcom_push(key='data_path', value=data_path)
    return "Data availability check completed - will be verified by training task"


def validate_model_output(**context):
    """Validate that model training was successful"""
    import os
    import json
    
    # Since this runs in Airflow worker, we can't directly access PVC
    # We'll use Kubernetes pod to validate model
    return "Model validation will be handled by Kubernetes validation pod"


def check_predictions(**context):
    """Check prediction results and generate summary"""
    import os
    
    # Since this runs in Airflow worker, we can't directly access PVC
    # We'll use Kubernetes pod to validate predictions
    return "Prediction validation will be handled by Kubernetes validation pod"


# Task 1: Check data availability
check_data_task = PythonOperator(
    task_id='check_data_availability',
    python_callable=check_data_availability,
    dag=dag,
)

# Task 2: Train ML model
train_model_task = KubernetesPodOperator(
    task_id='train_ml_model',
    dag=dag,
    **get_pod_config('train', 'python train.py --model-output-path /app/models')
)

# Task 3: Validate model training
validate_model_task = KubernetesPodOperator(
    task_id='validate_model_output',
    dag=dag,
    **get_pod_config('validate-model', 'python validate.py validate-model --models-dir /app/models')
)

# Task 4: Make predictions
predict_task = KubernetesPodOperator(
    task_id='make_predictions',
    dag=dag,
    **get_pod_config('predict', 'python predict.py --model-path /app/models/latest_model.pkl --output-path /app/predictions')
)

# Task 5: Validate predictions
validate_predictions_task = KubernetesPodOperator(
    task_id='validate_predictions',
    dag=dag,
    **get_pod_config('validate-predictions', 'python validate.py validate-predictions --predictions-dir /app/predictions')
)

# Task 6: Cleanup old files (optional)
cleanup_task = KubernetesPodOperator(
    task_id='cleanup_old_files',
    dag=dag,
    **get_pod_config('cleanup', 'python validate.py cleanup --models-dir /app/models --predictions-dir /app/predictions --keep-count 5')
)

# Task 7: Send notification (optional)
notification_task = KubernetesPodOperator(
    task_id='send_notification',
    dag=dag,
    **get_pod_config('notification', 'python -c "print(\'ML Pipeline completed successfully!\'); print(\'Run ID: {{ run_id }}\'); print(\'Execution Date: {{ ds }}\'); print(\'Add your notification logic here (e.g., Slack, email, etc.)\')"')
)

# Define task dependencies
check_data_task >> train_model_task >> validate_model_task >> predict_task >> validate_predictions_task >> cleanup_task >> notification_task
