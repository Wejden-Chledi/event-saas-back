from storages.backends.azure_storage import AzureStorage


class AzureMediaStorage(AzureStorage):
    account_name = None
    account_key = None
    azure_container = None
    expiration_secs = None