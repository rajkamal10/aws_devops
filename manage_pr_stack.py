import boto3, os, sys, yaml
from botocore.exceptions import ClientError

with open("values.yml") as f:
    values = yaml.safe_load(f)

stack_config = values["stacks"]["s3-app"]
region = stack_config["region"]
template_file = stack_config["template"]
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

def deploy_stack():
    body = open(template_file).read()
    if stack_exists(stack_name):
        print(f"Updating stack {stack_name}...")
        cf.update_stack(StackName=stack_name,
                        TemplateBody=body,
                        Capabilities=["CAPABILITY_NAMED_IAM"])
    else:
        print(f"Creating stack {stack_name}...")
        cf.create_stack(StackName=stack_name,
                        TemplateBody=body,
                        Capabilities=["CAPABILITY_NAMED_IAM"])

def delete_stack():
    if stack_exists(stack_name):
        print(f"Deleting stack {stack_name}...")
        cf.delete_stack(StackName=stack_name)

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "deploy"
    if action == "deploy":
        deploy_stack()
    elif action == "delete":
        delete_stack()
