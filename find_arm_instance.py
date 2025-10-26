import oci
import time
import logging
import random

# --- Configuration ---
CONFIG_FILE_LOCATION = "./.oci/config"
config = oci.config.from_file(file_location=CONFIG_FILE_LOCATION)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Your Specific Details (You have already filled these correctly) ---
COMPARTMENT_ID = "ocid1.tenancy.oc1..aaaaaaaa3oxicgu6m64teulopbk5f54xxfnxzbenlmiqejld2b5fxtaiacaa"
# CRITICAL: You correctly found your unique Availability Domain name
AVAILABILITY_DOMAIN = "ZLsV:AP-MUMBAI-1-AD-1"
IMAGE_ID = "ocid1.image.oc1.ap-mumbai-1.aaaaaaaaqh7ossbucbq74qhwvq7ies63x6wui2md36ysokjzs6wcwj5womeq"
SUBNET_ID = "ocid1.subnet.oc1.ap-mumbai-1.aaaaaaaa3xdyoq3fzizw27m3whxmo7y6sblo2pmpkago5yger46oogvtofdq"
SSH_PUBLIC_KEY = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDfwHU9h6UFydsUE+QkE2FvECs22OgirdXcPDsl8OB095T8YBXuvzMrT2acaOfIi3JdTJjs8YLBWSGyIV/V797xHEbq8PptnSbLxKlAThqVMHV9qE9dqIHjpsoIhW9c7emqGdbt8wvhBAwGlDJIwd+/Iml/3nqqlFcBhyok0PLMtxPl2ALmgVbwz8oSKujY/KTGCNvcu4bVR3c1UyLjbBPL2HyOsqtj8LtW0bh5aNNMAIRBvrobBnXX0vMh2PIuAC4PdNODeS7qz81HJuWtRu1HJbSFPgZEGO7Gj8xpyyARsDtuFnvLsd3LuugIXxjuQDeLD67BGd4brbuOSxZ6Ps2fMwJpZNo7liLHoEZVC4F7mzrXQI7SYNsvPjkqk4cb+zv5jOQFfzq8O5oohCEOki30CLII2kAYS0zutglEcsGDIeqA/35XJ0gVFgR6vM4ve+SLjCtRXbxLM+6HP5Vadh8y9Zt5uTJglgiRrxZ+27ompiAWFAA9b71SgxW+mLqzo0vDxZNDdIdEIAorc3iLhC++/g+oXnaDrhogokpaWE6vLIHBiH2jrfYNgeBtGTJnZrEJJ+dWV5aCCPjweJu24MTE1St9/UMbVKxeY/TpYhhpRfoui1ryw0Y37PAKADbhXrqL2SOP5HGf19c8vTmbMQn+4q8pvJ2iU7UlNAElqXTvqw== hamza@DESKTOP-HQOUFCO"

# --- Instance Details ---
INSTANCE_SHAPE = "VM.Standard.A1.Flex"
INSTANCE_OCPUS = 4
INSTANCE_MEMORY_GB = 24
INSTANCE_DISPLAY_NAME = "Automated-ARM-Instance"
# -----------------------------------------------------------------------------

compute_client = oci.core.ComputeClient(config)

logging.info(f"Starting script to find available ARM instance...")
logging.info(f"Target AD: {AVAILABILITY_DOMAIN}")
logging.info(f"Shape: {INSTANCE_SHAPE} ({INSTANCE_OCPUS} OCPUs, {INSTANCE_MEMORY_GB} GB RAM)")

while True:
    try:
        launch_instance_details = oci.core.models.LaunchInstanceDetails(
            compartment_id=COMPARTMENT_ID,
            availability_domain=AVAILABILITY_DOMAIN,
            shape=INSTANCE_SHAPE,
            shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
                ocpus=INSTANCE_OCPUS,
                memory_in_gbs=INSTANCE_MEMORY_GB
            ),
            display_name=INSTANCE_DISPLAY_NAME,
            source_details=oci.core.models.InstanceSourceViaImageDetails(
                image_id=IMAGE_ID
            ),
            create_vnic_details=oci.core.models.CreateVnicDetails(
                subnet_id=SUBNET_ID
            ),
            metadata={
                "ssh_authorized_keys": SSH_PUBLIC_KEY
            }
        )

        logging.info("Attempting to launch instance...")
        launch_response = compute_client.launch_instance(launch_instance_details)

        logging.info("SUCCESS! Instance launch request accepted.")
        logging.info(f"Instance OCID: {launch_response.data.id}")
        logging.info("Script will now terminate.")
        break

    except oci.exceptions.ServiceError as e:
        # =================================================================
        # === FINAL FIX: Make this check more general for any capacity error ===
        if "capacity" in e.message.lower():
            wait_seconds = random.randint(180, 420)
            logging.warning(f"Out of capacity in {AVAILABILITY_DOMAIN}. Retrying in {wait_seconds} seconds ({wait_seconds/60:.1f} minutes)...")
            time.sleep(wait_seconds)
        # =================================================================
        else:
            logging.error(f"An unexpected API error occurred: {e}")
            logging.error("Terminating script due to unexpected error.")
            break

    except Exception as e:
        logging.error(f"A fatal script error occurred: {e}")
        break
