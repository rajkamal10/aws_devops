import boto3
import os
import yaml
import sys
from botocore.exceptions import ClientError

# Load stack configuration
with open("values.yml") as f:
    values = yaml.safe_load(f)

# Require a stack key argument
if len(sys.argv) < 2:
    print("❌ Please provide a stack key (e.g., dynamo_db, s3_app).")
    sys.exit(1)

stack_key = sys.argv[1]
if stack_key not in values["stacks"]:
    print(f"❌ Stack key '{stack_key}' not found in values.yml.")
    sys.exit(1)

stack_config = values["stacks"][stack_key]

region = stack_config["region"]
template_file = stack_config["template"]
base_name = stack_config["base_name"]

pr_number = os.getenv("PR_NUMBER")
stack_name = f"{base_name}-pr{pr_number}" if pr_number else base_name

cf = boto3.client("cloudformation", region_name=region)

def stack_exists(name):
    try:
        cf.describe_stacks(StackName=name)
        return True
    except ClientError as e:
        if "does not exist" in str(e):
            return False
        raise

def deploy_stack():
    body = open(template_file).read()
    parameters = [
        {"ParameterKey": k, "ParameterValue": str(v)}
        for k, v in stack_config.items()
        if k not in ["template", "region", "base_name"]
    ]

    if stack_exists(stack_name):
        print(f"➡️ Deploying: Updating stack {stack_name}...")
        try:
            cf.update_stack(
                StackName=stack_name,
                TemplateBody=body,
                Parameters=parameters,
                Capabilities=["CAPABILITY_NAMED_IAM"]
            )
            waiter = cf.get_waiter("stack_update_complete")
            waiter.wait(StackName=stack_name)
            print(f"✅ Stack {stack_name} updated successfully.")
        except ClientError as e:
            if "No updates are to be performed" in str(e):
                print(f"⚠️ No changes detected for {stack_name}. Skipping update.")
            else:
                raise
    else:
        print(f"➡️ Deploying: Creating stack {stack_name}...")
        cf.create_stack(
            StackName=stack_name,
            TemplateBody=body,
            Parameters=parameters,
            Capabilities=["CAPABILITY_NAMED_IAM"]
        )
        waiter = cf.get_waiter("stack_create_complete")
        waiter.wait(StackName=stack_name)
        print(f"✅ Stack {stack_name} created successfully.")

if __name__ == "__main__":
    deploy_stack()
