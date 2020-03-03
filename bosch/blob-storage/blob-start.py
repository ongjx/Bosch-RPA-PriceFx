import os, uuid
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

try:
    print("Azure Blob storage v12 - Python quickstart sample")
    # Quick start code goes here
    connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    container_name = 'dataset'

    data_path = os.path.join(os.getcwd(),'data')

    for file in os.listdir(data_path):
        try:
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=file)
            file_dir = os.path.join(data_path, file)
            print('Uploading file from', file_dir)
            with open(file_dir, "rb") as data:
                blob_client.upload_blob(data, blob_type="BlockBlob")
        except Exception as e:
            print('Exception')
            print('continuing..')
except Exception as ex:
    print('Exception:')
    print(ex)
