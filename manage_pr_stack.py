import boto3
import os
import sys
import yaml
from botocore.exceptions import ClientError

# Load all stack configurations from values.yml
with open("values.yml") as f:
    values = yaml.safe_load(f)

def stack_exists(cf, name):
    try:
        cf.describe_stacks(StackName=name)
        return True
    except ClientError as e:
        if "does not exist" in str(e):
            return False
        raise

def deploy_stack(stack_name, template_file, region):
    cf = boto3.client("cloudformation", region_name=region)
    body = open(template_file).read()

    if stack_exists(cf, stack_name):
        print(f"🔄 Stack {stack_name} already exists.")
        print(f"➡️ Action: Stack {stack_name} will be UPDATED.")
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
        print(f"🆕 Stack {stack_name} does not exist.")
        print(f"➡️ Action: Stack {stack_name} will be CREATED.")
        cf.create_stack(
            StackName=stack_name,
            TemplateBody=body,
            Capabilities=["CAPABILITY_NAMED_IAM"]
        )
        waiter = cf.get_waiter("stack_create_complete")
        waiter.wait(StackName=stack_name)
        print(f"✅ Stack {stack_name} created successfully.")

def delete_stack(stack_name, region):
    cf = boto3.client("cloudformation", region_name=region)
    if stack_exists(cf, stack_name):
        print(f"🗑️ Stack {stack_name} exists.")
        print(f"➡️ Action: Stack {stack_name} will be DELETED.")
        cf.delete_stack(StackName=stack_name)
        waiter = cf.get_waiter("stack_delete_complete")
        waiter.wait(StackName=stack_name)
        print(f"✅ Stack {stack_name} deleted successfully.")
    else:
        print(f"⚠️ Stack {stack_name} does not exist. Nothing to delete.")

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "deploy"
    pr_number = os.getenv("PR_NUMBER")

    for stack_key, stack_config in values["stacks"].items():
        region = stack_config["region"]
        template_file = stack_config["template"]
        base_name = stack_config["base_name"]

        stack_name = f"{base_name}-pr{pr_number}" if pr_number else base_name

        print(f"\n📌 Managing stack: {stack_name} (from {stack_key})")

        if action == "deploy":
            deploy_stack(stack_name, template_file, region)
        elif action == "delete":
            delete_stack(stack_name, region)
        else:
            print("Usage: manage_pr_stack.py [deploy|delete]")
