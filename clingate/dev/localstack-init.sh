#!/bin/sh
# Runs inside LocalStack when it is ready. Mirrors the AWS resources the apps expect.
set -eu
awslocal s3api create-bucket --bucket clingate-raw-dev
awslocal sqs create-queue --queue-name clingate-ingest-dlq
awslocal sqs create-queue --queue-name clingate-export-dlq
DLQ_I=$(awslocal sqs get-queue-attributes --queue-url http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/clingate-ingest-dlq --attribute-names QueueArn --query Attributes.QueueArn --output text)
DLQ_E=$(awslocal sqs get-queue-attributes --queue-url http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/clingate-export-dlq --attribute-names QueueArn --query Attributes.QueueArn --output text)
awslocal sqs create-queue --queue-name clingate-ingest --attributes "{\"VisibilityTimeout\":\"60\",\"RedrivePolicy\":\"{\\\"deadLetterTargetArn\\\":\\\"$DLQ_I\\\",\\\"maxReceiveCount\\\":\\\"5\\\"}\"}"
awslocal sqs create-queue --queue-name clingate-export --attributes "{\"VisibilityTimeout\":\"60\",\"RedrivePolicy\":\"{\\\"deadLetterTargetArn\\\":\\\"$DLQ_E\\\",\\\"maxReceiveCount\\\":\\\"5\\\"}\"}"
