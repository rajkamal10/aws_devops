import boto3
import os
import sys
import yaml
from botocore.exceptions import ClientError

# Load stack configuration from values.yml
with open("values.yml") as f:
    values = yaml.safe_load(f)

stack_config = values["stacks"]["s3-app"]
region = stack_config["region"]
template_file = stack_config["template"]
base_name = stack_config["base_name"]

# Build stack name using PR number
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

def deploy_stack():
    body = open(template_file).read()
    if stack_exists(stack_name):
        print(f"Updating stack {stack_name}...")
        try:
            cf.update_stack(
                StackName=stack_name,
                TemplateBody=body,
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
        print(f"Creating stack {stack_name}...")
        cf.create_stack(
            StackName=stack_name,
            TemplateBody=body,
            Capabilities=["CAPABILITY_NAMED_IAM"]
        )
        waiter = cf.get_waiter("stack_create_complete")
        waiter.wait(StackName=stack_name)
        print(f"✅ Stack {stack_name} created successfully.")

    # Always print the stack name at the end
    print(f"📌 Managed stack: {stack_name}")

def delete_stack():
    if stack_exists(stack_name):
        print(f"Deleting stack {stack_name}...")
        cf.delete_stack(StackName=stack_name)
        waiter = cf.get_waiter("stack_delete_complete")
        waiter.wait(StackName=stack_name)
        print(f"🗑️ Stack {stack_name} deleted successfully.")
    else:
        print(f"⚠️ Stack {stack_name} does not exist. Nothing to delete.")

    # Always print the stack name at the end
    print(f"📌 Managed stack: {stack_name}")

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "deploy"
    if action == "deploy":
        deploy_stack()
    elif action == "delete":
        delete_stack()
    else:
        print("Usage: manage_pr_stack.py [deploy|delete]")
