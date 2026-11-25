pipeline {
  agent any
  environment {
    AWS_DEFAULT_REGION = 'us-east-1'
    BUCKET_NAME        = 'tanya-file-mover-bucket'
    LAMBDA_ROLE_ARN    = 'arn:aws:iam::<account-id>:role/file-mover-role'
  }
  stages {
    stage('Checkout') { steps { checkout scm } }
    stage('Setup Python') {
      steps { sh 'python3 -m venv venv && . venv/bin/activate && pip install boto3' }
    }
    stage('Deploy') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'aws-creds',
            usernameVariable: 'AWS_ACCESS_KEY_ID',
            passwordVariable: 'AWS_SECRET_ACCESS_KEY')]) {
          sh '. venv/bin/activate && python deploy.py'
        }
      }
    }
  }
}