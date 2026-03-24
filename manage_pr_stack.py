import boto3
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
        if e.response["Error"]["Code"] == "ValidationError":
            return False
        raise

def deploy_stack(cf, stack_name, stack_config):
    template_body = open(stack_config["template"]).read()
    parameters = [
        {"ParameterKey": k, "ParameterValue": str(v)}
        for k, v in stack_config.items()
        if k not in ("template", "region", "base_name")
    ]

    if stack_exists(cf, stack_name):
        print(f"🔄 Updating stack {stack_name}...")
        try:
            cf.update_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=parameters,
                Capabilities=["CAPABILITY_NAMED_IAM"]
            )
        except ClientError as e:
            if "No updates are to be performed" in str(e):
                print("ℹ️ No changes detected.")
            else:
                raise
    else:
        print(f"🆕 Creating stack {stack_name}...")
        cf.create_stack(
            StackName=stack_name,
            TemplateBody=template_body,
            Parameters=parameters,
            Capabilities=["CAPABILITY_NAMED_IAM"]
        )

def delete_stack(cf, stack_name):
    if stack_exists(cf, stack_name):
        print(f"🗑️ Deleting stack {stack_name}...")
        cf.delete_stack(StackName=stack_name)
    else:
        print(f"⚠️ Stack {stack_name} does not exist.")

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "deploy"

    for stack_key, stack_config in values["stacks"].items():
        region = stack_config["region"]
        stack_name = stack_config["base_name"]
        cf = boto3.client("cloudformation", region_name=region)

        print(f"\n📌 Processing stack: {stack_name} (from {stack_key})")

        if action == "deploy":
            deploy_stack(cf, stack_name, stack_config)
        elif action == "delete":
            delete_stack(cf, stack_name)
        else:
            print("Usage: manage_pr_stack.py [deploy|delete]")
