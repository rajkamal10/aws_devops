import boto3
import os
import yaml
from botocore.exceptions import ClientError

with open("values.yml") as f:
    values = yaml.safe_load(f)

stack_config = values["stacks"]["s3-app"]
region = stack_config["region"]
base_name = stack_config["base_name"]

pr_number = os.getenv("PR_NUMBER")
stack_name = f"{base_name}-pr{pr_number}"

cf = boto3.client("cloudformation", region_name=region)

def stack_exists(name):
    try:
        cf.describe_stacks(StackName=name)
        return True
    except ClientError as e:
        if "does not exist" in str(e):
            return False
        raise

if __name__ == "__main__":
    if stack_exists(stack_name):
        print(f"🔄 Stack {stack_name} already exists.")
        print(f"🚀 Stack status for this PR:\n➡️ Action: Stack {stack_name} will be UPDATED.")
    else:
        print(f"🆕 Stack {stack_name} does not exist.")
        print(f"🚀 Stack status for this PR:\n➡️ Action: Stack {stack_name} will be CREATED.")
