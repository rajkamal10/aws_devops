import boto3, yaml

with open("values.yml") as f:
    values = yaml.safe_load(f)

stack_config = values["stacks"]["s3-app"]
region = stack_config["region"]
template_file = stack_config["template"]
stack_name = stack_config["base_name"]

cf = boto3.client("cloudformation", region_name=region)

def deploy_stack():
    body = open(template_file).read()
    try:
        cf.describe_stacks(StackName=stack_name)
        print(f"Updating stack {stack_name}...")
        cf.update_stack(StackName=stack_name,
                        TemplateBody=body,
                        Capabilities=["CAPABILITY_NAMED_IAM"])
    except:
        print(f"Creating stack {stack_name}...")
        cf.create_stack(StackName=stack_name,
                        TemplateBody=body,
                        Capabilities=["CAPABILITY_NAMED_IAM"])

if __name__ == "__main__":
    deploy_stack()
