import oci
import time
import logging
import random
import sys

# --- Configuration ---
CONFIG_FILE_LOCATION = "./.oci/config"

# Setup logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('oci_instance_launch.log')
    ]
)

# --- Your Specific Details ---
COMPARTMENT_ID = "ocid1.tenancy.oc1..aaaaaaaa3oxicgu6m64teulopbk5f54xxfnxzbenlmiqejld2b5fxtaiacaa"
AVAILABILITY_DOMAIN = "ZLsV:AP-MUMBAI-1-AD-1"
IMAGE_ID = "ocid1.image.oc1.ap-mumbai-1.aaaaaaaaqh7ossbucbq74qhwvq7ies63x6wui2md36ysokjzs6wcwj5womeq"
SUBNET_ID = "ocid1.subnet.oc1.ap-mumbai-1.aaaaaaaa3xdyoq3fzizw27m3whxmo7y6sblo2pmpkago5yger46oogvtofdq"
SSH_PUBLIC_KEY = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDfwHU9h6UFydsUE+QkE2FvECs22OgirdXcPDsl8OB095T8YBXuvzMrT2acaOfIi3JdTJjs8YLBWSGyIV/V797xHEbq8PptnSbLxKlAThqVMHV9qE9dqIHjpsoIhW9c7emqGdbt8wvhBAwGlDJIwd+/Iml/3nqqlFcBhyok0PLMtxPl2ALmgVbwz8oSKujY/KTGCNvcu4bVR3c1UyLjbBPL2HyOsqtj8LtW0bh5aNNMAIRBvrobBnXX0vMh2PIuAC4PdNODeS7qz81HJuWtRu1HJbSFPgZEGO7Gj8xpyyARsDtuFnvLsd3LuugIXxjuQDeLD67BGd4brbuOSxZ6Ps2fMwJpZNo7liLHoEZVC4F7mzrXQI7SYNsvPjkqk4cb+zv5jOQFfzq8O5oohCEOki30CLII2kAYS0zutglEcsGDIeqA/35XJ0gVFgR6vM4ve+SLjCtRXbxLM+6HP5Vadh8y9Zt5uTJglgiRrxZ+27ompiAWFAA9b71SgxW+mLqzo0vDxZNDdIdEIAorc3iLhC++/g+oXnaDrhogokpaWE6vLIHBiH2jrfYNgeBtGTJnZrEJJ+dWV5aCCPjweJu24MTE1St9/UMbVKxeY/TpYhhpRfoui1ryw0Y37PAKADbhXrqL2SOP5HGf19c8vTmbMQn+4q8pvJ2iU7UlNAElqXTvqw== hamza@DESKTOP-HQOUFCO"

# --- Instance Details ---
INSTANCE_SHAPE = "VM.Standard.A1.Flex"
INSTANCE_OCPUS = 4
INSTANCE_MEMORY_GB = 24
INSTANCE_DISPLAY_NAME = "Automated-ARM-Instance"

# --- Retry Configuration ---
MAX_RETRIES = 100000  # Prevent infinite loops (adjust as needed)
MIN_WAIT_SHORT = 180  # 3 minutes
MAX_WAIT_SHORT = 240  # 4 minutes
MIN_WAIT_LONG = 240   # 4 minutes
MAX_WAIT_LONG = 360   # 6 minutes
SHORT_WAIT_PROBABILITY = 0.75  # 75% chance of short wait


def validate_config():
    """Validate configuration before starting"""
    try:
        config = oci.config.from_file(file_location=CONFIG_FILE_LOCATION)
        oci.config.validate_config(config)
        logging.info("✓ OCI configuration validated successfully")
        return config
    except Exception as e:
        logging.error(f"Configuration validation failed: {e}")
        sys.exit(1)


def calculate_retry_wait(attempt_num):
    """Calculate wait time with weighted randomization"""
    if random.random() < SHORT_WAIT_PROBABILITY:
        wait = random.randint(MIN_WAIT_SHORT, MAX_WAIT_SHORT)
        category = "short"
    else:
        wait = random.randint(MIN_WAIT_LONG, MAX_WAIT_LONG)
        category = "long"
    
    return wait, category


def create_launch_details():
    """Create instance launch configuration"""
    return oci.core.models.LaunchInstanceDetails(
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
            subnet_id=SUBNET_ID,
            assign_public_ip=True  # Explicitly request public IP
        ),
        metadata={
            "ssh_authorized_keys": SSH_PUBLIC_KEY
        }
    )


def main():
    """Main execution loop"""
    # Validate configuration
    config = validate_config()
    compute_client = oci.core.ComputeClient(config)
    
    logging.info("=" * 70)
    logging.info("Starting OCI ARM Instance Provisioning Script")
    logging.info("=" * 70)
    logging.info(f"Target AD: {AVAILABILITY_DOMAIN}")
    logging.info(f"Shape: {INSTANCE_SHAPE} ({INSTANCE_OCPUS} OCPUs, {INSTANCE_MEMORY_GB} GB RAM)")
    logging.info(f"Max retries: {MAX_RETRIES}")
    logging.info("=" * 70)
    
    attempt = 0
    start_time = time.time()
    
    try:
        while attempt < MAX_RETRIES:
            attempt += 1
            
            try:
                logging.info(f"[Attempt {attempt}/{MAX_RETRIES}] Launching instance...")
                
                launch_details = create_launch_details()
                launch_response = compute_client.launch_instance(launch_details)
                
                # Success!
                elapsed = time.time() - start_time
                logging.info("=" * 70)
                logging.info("✓ SUCCESS! Instance launched successfully")
                logging.info("=" * 70)
                logging.info(f"Instance OCID: {launch_response.data.id}")
                logging.info(f"Instance Name: {launch_response.data.display_name}")
                logging.info(f"Shape: {launch_response.data.shape}")
                logging.info(f"State: {launch_response.data.lifecycle_state}")
                logging.info(f"Total attempts: {attempt}")
                logging.info(f"Total time: {elapsed/60:.1f} minutes")
                logging.info("=" * 70)
                
                return 0
                
            except oci.exceptions.ServiceError as e:
                # Handle capacity errors
                if "capacity" in e.message.lower() or e.status == 500:
                    wait_time, wait_category = calculate_retry_wait(attempt)
                    
                    logging.warning(
                        f"⚠ No capacity available (attempt {attempt}/{MAX_RETRIES})"
                    )
                    logging.info(
                        f"Waiting {wait_time}s ({wait_time/60:.1f} min) "
                        f"[{wait_category} wait] before retry..."
                    )
                    
                    time.sleep(wait_time)
                    
                # Handle authentication/authorization errors
                elif e.status in [401, 403]:
                    logging.error(f"Authentication/Authorization error: {e.message}")
                    logging.error("Please check your OCI config and permissions")
                    return 1
                    
                # Handle not found errors
                elif e.status == 404:
                    logging.error(f"Resource not found: {e.message}")
                    logging.error("Please verify your OCID values")
                    return 1
                    
                # Handle other service errors
                else:
                    logging.error(f"API Error [{e.status}]: {e.message}")
                    logging.error(f"Code: {e.code}")
                    logging.error("Terminating due to unexpected error")
                    return 1
                    
            except KeyboardInterrupt:
                logging.info("\n⚠ Script interrupted by user (Ctrl+C)")
                elapsed = time.time() - start_time
                logging.info(f"Total attempts made: {attempt}")
                logging.info(f"Total runtime: {elapsed/60:.1f} minutes")
                return 130  # Standard exit code for SIGINT
                
            except Exception as e:
                logging.error(f"Unexpected error: {type(e).__name__}: {e}")
                logging.error("Terminating script")
                return 1
        
        # Max retries reached
        elapsed = time.time() - start_time
        logging.error("=" * 70)
        logging.error(f"✗ Maximum retry attempts ({MAX_RETRIES}) reached")
        logging.error(f"Total runtime: {elapsed/60:.1f} minutes")
        logging.error("No capacity found. Consider trying:")
        logging.error("  - Different availability domain")
        logging.error("  - Smaller instance configuration")
        logging.error("  - Different time of day")
        logging.error("=" * 70)
        return 1
        
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)