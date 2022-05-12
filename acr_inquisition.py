import json
import os

import sys
from typing import Optional

import click

# noinspection PyPackageRequirements,PyUnresolvedReferences
from azure.containerregistry import ContainerRegistryClient, ArtifactManifestProperties, ArtifactManifestProperties
# noinspection PyPackageRequirements
from azure.identity import DefaultAzureCredential

ACCOUNT_URL = os.environ.get("ACR_URL")
AZURE_AUDIENCE = "https://management.azure.com"
TIME_FMT = "%Y-%m-%d %H:%M:%S"


def check_endpoint():
    if not ACCOUNT_URL:
        sys.stderr.write("The URL endpoint of the Azure container registry must be set with environment variable ACR_URL\n")
        exit(1)


def get_acr_client(audience: str):
    client = ContainerRegistryClient(ACCOUNT_URL, DefaultAzureCredential(), audience=audience)
    return client


@click.group(context_settings={'help_option_names': ['-h', '--help']})
def cli():
    pass


@click.command(name='describe')
@click.argument("image", type=click.STRING, required=True)
@click.argument("tag", type=click.STRING, required=False, default="latest")
# @click.option('--pod-indices', "pod_indices", type=click.STRING, help="List of indices, e.g.: 2,3,6")
def describe_image(image: str, tag: str):
    """Describes a specific image."""
    acr_client = get_acr_client(AZURE_AUDIENCE)
    props: ArtifactManifestProperties = acr_client.get_manifest_properties(repository=image, tag_or_digest=tag)
    print("Image:       ", f"{image}:{tag}")
    print("Created on:  ", props.created_on)
    print("Last update: ", props.last_updated_on)
    print("Architecture:", props.architecture)
    print("OS:          ", props.operating_system)
    print("Size:        ", f"{props.size / 1024 ** 2:.0f} MBytes")


@click.command(name='list')
@click.argument("repository", type=click.STRING, required=False, default="data-services")
@click.option('--size-not-null', "size_not_null", is_flag=True, help="Do not list images with a size of zero")
@click.option('--sort', "sort_order", type=click.STRING, help="Sorting order: 'created_on'")
def list_manifests(repository: str, size_not_null: bool, sort_order: Optional[str]):
    """Displays a listing of images in an Azure container registry."""
    acr_client = get_acr_client(AZURE_AUDIENCE)

    manifests = []

    for item in acr_client.list_manifest_properties(repository):
        item: ArtifactManifestProperties
        log = {
            "created_on": item.created_on.strftime(TIME_FMT),
            "last_update": item.last_updated_on.strftime(TIME_FMT),
            "registry": item.repository_name,
            "sha256": item.digest,
            "size": item.size / 1024 ** 2,
            "tags": item.tags or []
        }

        manifests.append(log)

    if size_not_null:
        def has_size(val):
            return val["size"] > 0

        manifests = filter(has_size, manifests)

    if sort_order == "created_on":
        def sort_created_on(val):
            return val["created_on"]
        manifests = sorted(manifests, key=sort_created_on)
    elif sort_order is None:
        pass
    else:
        raise ValueError(f"Bad value: {sort_order}")

    print(json.dumps(manifests))


@click.command()
@click.pass_context
def help_syntax(ctx):
    """Displays help with syntax details"""
    examples = """
Examples:
    python acr_inquisition.py list [<repository> = "data-services"]
    python acr_inquisition.py list --size-not-null --sort "created_on" [<repository> = "data-services"]
    python acr_inquisition.py list <repository>
    python acr_inquisition.py describe <image> [<tag> = "latest"]
    """
    print(ctx.parent.get_help())
    print(examples)


cli.add_command(help_syntax)
cli.add_command(describe_image)
cli.add_command(list_manifests)

if __name__ == '__main__':
    check_endpoint()
    cli()
