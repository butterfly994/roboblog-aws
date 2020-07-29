REGION="YOUR_REGION"
IMAGE_NAME="YOUR_IMAGE_NAME"
REPOSITORY_NAME="YOUR_REPOSITORY_NAME"
ACCOUNT_ID="YOUR_ACCOUNT_ID"

login:
	aws ecr get-login-password --region $(REGION) | docker login --username AWS --password-stdin $(ACCOUNT_ID).dkr.ecr.$(REGION).amazonaws.com

build:
	docker build -t $(IMAGE_NAME):latest .

retag:
	docker tag $(IMAGE_NAME):latest $(ACCOUNT_ID).dkr.ecr.$(REGION).amazonaws.com/$(REPOSITORY_NAME):latest

push:
	docker push $(ACCOUNT_ID).dkr.ecr.$(REGION).amazonaws.com/$(REPOSITORY_NAME):latest
