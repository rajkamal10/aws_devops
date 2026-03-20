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

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "deploy"

    for stack_key, stack_config in values["stacks"].items():
        region = stack_config["region"]
        base_name = stack_config["base_name"]

        # ✅ No PR number appended
        stack_name = base_name
        cf = boto3.client("cloudformation", region_name=region)

        print(f"\n📌 Checking stack: {stack_name} (from {stack_key})")

        if action == "deploy":
            if stack_exists(cf, stack_name):
                print(f"🔄 Stack {stack_name} already exists.")
                print(f"🚀 Stack status:\n➡️ Action: Stack {stack_name} would be UPDATED.")
            else:
                print(f"🆕 Stack {stack_name} does not exist.")
                print(f"🚀 Stack status:\n➡️ Action: Stack {stack_name} would be CREATED.")
        elif action == "delete":
            if stack_exists(cf, stack_name):
                print(f"🗑️ Stack {stack_name} exists.")
                print(f"🚀 Stack status:\n➡️ Action: Stack {stack_name} would be DELETED.")
            else:
                print(f"⚠️ Stack {stack_name} does not exist. Nothing to delete.")
        else:
            print("Usage: manage_pr_stack.py [deploy|delete]")
