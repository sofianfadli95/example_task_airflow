# Machine Learning Pipeline with Airflow

This project demonstrates a complete machine learning pipeline that runs in Docker containers orchestrated by Apache Airflow. The pipeline includes model training, prediction, and automated deployment using GitHub Actions.

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   GitHub Repo   │───▶│  GitHub Actions  │───▶│ Container Registry│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                          │
┌─────────────────┐    ┌──────────────────┐              │
│  Airflow DAGs   │───▶│   Airflow Tasks  │◄─────────────┘
└─────────────────┘    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  ML Containers   │
                    │  (Train/Predict) │
                    └──────────────────┘
```

## 📁 Project Structure

```
example_task_airflow/
├── ml_pipeline/
│   ├── train.py              # ML training script
│   ├── predict.py            # ML prediction script
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile           # Container definition
├── dags/
│   └── ml_pipeline_dag.py   # Airflow DAG definition
├── .github/workflows/
│   └── build-and-push.yml   # GitHub Actions workflow
├── docker-compose.yml       # Airflow setup
├── requirements.txt         # Project dependencies
└── README.md               # This file
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Git
- GitHub account (for container registry)

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd example_task_airflow

# Create required directories
mkdir -p data models predictions logs plugins config

# Set proper permissions (Linux/macOS)
echo "AIRFLOW_UID=$(id -u)" > .env
echo "AIRFLOW_PROJ_DIR=." >> .env
echo "_AIRFLOW_WWW_USER_USERNAME=airflow" >> .env
echo "_AIRFLOW_WWW_USER_PASSWORD=airflow" >> .env
```

### 2. Start Airflow

```bash
# Initialize Airflow database
docker compose up airflow-init

# Start Airflow services
docker compose up -d

# Check services are running
docker compose ps
```

### 3. Access Airflow UI

- URL: http://localhost:8080
- Username: `airflow`
- Password: `airflow`

### 4. Setup Kubernetes Resources (If using Kubernetes)

If you're running Airflow on Kubernetes and want to use KubernetesPodOperator:

```bash
# Create namespace and resources
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/service-account.yaml
kubectl apply -f k8s/persistent-volumes.yaml

# Verify resources
kubectl get pvc -n airflow
kubectl get serviceaccount -n airflow
```

### 5. Configure Airflow Variables

In the Airflow UI, go to Admin → Variables and set:

**For Docker setup:**
| Key | Value | Description |
|-----|-------|-------------|
| `ml_pipeline_image` | `ghcr.io/yourusername/yourrepo/ml-pipeline:latest` | Docker image for ML pipeline |
| `docker_network` | `airflow_default` | Docker network name |
| `data_volume` | `/opt/airflow/data` | Data volume path |
| `models_volume` | `/opt/airflow/models` | Models volume path |
| `predictions_volume` | `/opt/airflow/predictions` | Predictions volume path |

**For Kubernetes setup:**
| Key | Value | Description |
|-----|-------|-------------|
| `ml_pipeline_image` | `ghcr.io/yourusername/yourrepo/ml-pipeline:latest` | Docker image for ML pipeline |
| `kubernetes_namespace` | `airflow` | Kubernetes namespace |
| `service_account` | `airflow` | Service account name |
| `pvc_data` | `airflow-data-pvc` | Data PVC name |
| `pvc_models` | `airflow-models-pvc` | Models PVC name |
| `pvc_predictions` | `airflow-predictions-pvc` | Predictions PVC name |

## 🔧 Building and Deploying

### Local Development

Build the ML pipeline image locally:

```bash
cd ml_pipeline
docker build -t ml-pipeline:local .

# Test the container
docker run --rm -v $(pwd)/../models:/app/models ml-pipeline:local python train.py
docker run --rm -v $(pwd)/../models:/app/models -v $(pwd)/../predictions:/app/predictions ml-pipeline:local python predict.py
```

### GitHub Actions Deployment

1. **Enable GitHub Container Registry:**
   - Go to your GitHub repository settings
   - Navigate to Actions → General
   - Enable "Read and write permissions" for GITHUB_TOKEN

2. **Update Image Reference:**
   - Edit `.github/workflows/build-and-push.yml`
   - Replace `${{ github.repository }}` with your actual repository name
   - Update the Airflow variable `ml_pipeline_image` to match

3. **Push Changes:**
   ```bash
   git add .
   git commit -m "Add ML pipeline with Airflow"
   git push origin main
   ```

4. **Monitor Build:**
   - Go to GitHub Actions tab
   - Watch the "Build and Push ML Pipeline Docker Image" workflow
   - Once complete, the image will be available in your GitHub Container Registry

## 📊 ML Pipeline Details

### Training Pipeline (`train.py`)

- **Features:** Generates sample classification data or loads from CSV
- **Model:** Random Forest Classifier
- **Output:** Trained model (`.pkl`) and metrics (`.json`)
- **Configurable:** Model parameters, data paths, output locations

**Usage:**
```bash
python train.py --data-path /app/data/training_data.csv --model-output-path /app/models
```

### Prediction Pipeline (`predict.py`)

- **Input:** Trained model and new data
- **Output:** Predictions with confidence scores
- **Format:** CSV with predictions and probabilities

**Usage:**
```bash
python predict.py --model-path /app/models/latest_model.pkl --data-path /app/data/new_data.csv --output-path /app/predictions
```

## 🔄 Airflow DAG Workflow

The `ml_pipeline` DAG includes:

1. **check_data_availability** - Verify training data exists
2. **train_ml_model** - Train the ML model using Docker container
3. **validate_model_output** - Check model quality and metrics
4. **make_predictions** - Generate predictions using trained model
5. **validate_predictions** - Verify prediction output
6. **cleanup_old_files** - Remove old model/prediction files
7. **send_notification** - Send completion notification

### DAG Configuration

- **Schedule:** Daily (`timedelta(days=1)`)
- **Retries:** 2 with 5-minute delay
- **Max Active Runs:** 1
- **Tags:** `['ml', 'training', 'prediction']`
- **Execution Environment:** Kubernetes Pods (using KubernetesPodOperator)

### Kubernetes Features

- **Resource Management:** CPU and memory limits/requests for each task
- **Persistent Storage:** Shared data across tasks using PVCs
- **Isolation:** Each task runs in a separate pod
- **Scalability:** Automatic pod scheduling and cleanup
- **Security:** RBAC with dedicated service accounts

## 📂 Data Management

### Directory Structure

```
/opt/airflow/
├── data/           # Training and input data
├── models/         # Trained models and metrics
└── predictions/    # Prediction outputs
```

### Data Formats

**Training Data (`training_data.csv`):**
```csv
feature_0,feature_1,...,feature_19,target
0.123,0.456,...,0.789,1
-0.321,0.654,...,-0.987,0
```

**Prediction Output:**
```csv
feature_0,feature_1,...,predicted_class,prediction_confidence,prob_class_0,prob_class_1,prediction_timestamp
0.123,0.456,...,1,0.85,0.15,0.85,2024-01-15T10:30:00
```

## 🛠️ Customization

### Adding New Features

1. **Modify ML Scripts:**
   - Update `train.py` for new model types or preprocessing
   - Update `predict.py` for new prediction logic

2. **Update DAG:**
   - Add new tasks to `ml_pipeline_dag.py`
   - Modify task dependencies as needed

3. **Rebuild Container:**
   - Push changes to trigger GitHub Actions
   - Update Airflow variable with new image tag

### Configuration Options

**Environment Variables:**
- `PYTHONUNBUFFERED=1` - Real-time logging
- `AIRFLOW_RUN_ID` - Airflow execution context
- `EXECUTION_DATE` - DAG execution date

**Docker Mounts:**
- `/app/data` - Input data directory
- `/app/models` - Model storage directory
- `/app/predictions` - Prediction output directory

## 🔍 Monitoring and Troubleshooting

### Logs

**Airflow Logs:**
```bash
# View DAG logs
docker compose logs airflow-scheduler

# View task logs in Airflow UI
# Navigate to DAG → Task → Logs
```

**Container Logs:**
```bash
# Check Docker container logs
docker logs <container_id>

# Real-time logs during execution
docker compose logs -f
```

### Common Issues

1. **Permission Errors:**
   ```bash
   # Fix ownership
   sudo chown -R $USER:$USER data models predictions logs
   ```

2. **Docker Socket Access:**
   ```bash
   # Add user to docker group
   sudo usermod -aG docker $USER
   # Restart terminal/session
   ```

3. **Memory Issues:**
   ```bash
   # Increase Docker memory allocation
   # Docker Desktop: Settings → Resources → Memory
   ```

### Health Checks

```bash
# Check Airflow services
curl http://localhost:8080/health

# Check database connection
docker compose exec postgres pg_isready -U airflow

# Verify DAG syntax
docker compose exec airflow-webserver airflow dags check ml_pipeline
```

## 📈 Scaling and Production

### High Availability

1. **Use external database** (PostgreSQL, MySQL)
2. **Add Redis for Celery** (if using CeleryExecutor)
3. **Load balancer** for multiple webserver instances

### Security

1. **Secrets Management:**
   - Use Airflow Connections for sensitive data
   - Environment variables for configuration
   - External secret managers (AWS Secrets Manager, HashiCorp Vault)

2. **Network Security:**
   - Restrict container network access
   - Use private container registries
   - Implement proper authentication

### Monitoring

1. **Metrics Collection:**
   - Airflow StatsD integration
   - Custom metrics in ML scripts
   - Container resource monitoring

2. **Alerting:**
   - Email notifications on failures
   - Slack/Teams integration
   - PagerDuty for critical issues

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Resources

- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [scikit-learn Documentation](https://scikit-learn.org/stable/)
