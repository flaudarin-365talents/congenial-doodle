import argparse
import os

import sys

# noinspection PyPackageRequirements,PyUnresolvedReferences
from azure.containerregistry import ContainerRegistryClient, ArtifactManifestProperties, ArtifactManifestProperties
# noinspection PyPackageRequirements
from azure.identity import DefaultAzureCredential

account_url = os.environ.get("ACR_URL")


def check_endpoint():
    if not account_url:
        sys.stderr.write("The URL endpoint of the Azure container registry must be set with environment variable ACR_URL\n")
        exit(1)


if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description="Get info from Azure container registry")
    argparser.add_argument("--image-tag", required=False, nargs=2, help="e.g. --image-tag my-image-name version-tag")
    argparser.add_argument("--repository", required=False, help="Repository name within the registry "
                                                                "(image name w/o tag)")

    args = argparser.parse_args()

    audience = "https://management.azure.com"
    client = ContainerRegistryClient(account_url, DefaultAzureCredential(), audience=audience)

    if args.image_tag:
        image, tag = args.image_tag
        props: ArtifactManifestProperties = client.get_manifest_properties(repository=image, tag_or_digest=tag)
        print("Image:       ", f"{image}:{tag}")
        print("Created on:  ", props.created_on)
        print("Last update: ", props.last_updated_on)
        print("Architecture:", props.architecture)
        print("OS:          ", props.operating_system)
        print("Size:        ", f"{props.size / 1024 ** 2:.0f} MBytes")
    else:
        repository = args.repository or "data-services"

        for item in client.list_manifest_properties(repository):
            item: ArtifactManifestProperties
            if item.tags:
                tag = "|".join(item.tags)
            else:
                tag = ""
            size = item.size / 1024 ** 2
            print(f"{item.repository_name}:{tag}    {size} MB    ref={item.digest}")
