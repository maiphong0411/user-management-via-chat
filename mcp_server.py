import subprocess
import platform
import logging
import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


# Load environment variables from .env file
load_dotenv()

# Get sudo password from the .env file
SUDO_PASSWORD = os.getenv("SUDO_PASSWORD")

# Default password for the user
DEFAULT_PASSWORD = "20252025"

# Initialize FastMCP server
mcp = FastMCP("user-management")

# Configure logger
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def run_sudo_command(command: list):
    """
    Run a sudo command with the sudo password supplied from .env
    """
    try:
        command_with_sudo = f'echo {SUDO_PASSWORD} | sudo -S {" ".join(command)}'
        subprocess.run(command_with_sudo, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Error while executing command: {e}")
        raise


@mcp.tool()
def create_user(username: str) -> str:
    """
    Create a new standard (non-admin) user on macOS or Ubuntu with a default password "20252025",
    and require the user to change the password at the first login.

    Parameters:
    ----------
    username : str
        Username of the new user account.

    Returns:
    -------
    str
        Message indicating success or failure.
    """
    system = platform.system()

    logging.info(f"Detected OS: {system}")
    logging.info(f"Starting user creation for '{username}'...")

    try:
        if system == "Darwin":  # macOS
            full_name = username.capitalize()
            logging.info("Creating user on macOS...")

            # Create user using sysadminctl
            run_sudo_command(
                [
                    "sysadminctl",
                    "-addUser",
                    username,
                    "-fullName",
                    full_name,
                    "-password",
                    DEFAULT_PASSWORD,
                ]
            )
            logging.info("User created successfully on macOS.")

            # Force password change at first login
            logging.info("Forcing password change at first login (macOS)...")
            run_sudo_command(
                ["pwpolicy", "-u", username, "-setpolicy", "newPasswordRequired=1"]
            )
            logging.info("Password policy applied successfully.")

        elif system == "Linux":  # Ubuntu
            logging.info("Creating user on Linux...")
            run_sudo_command(["useradd", "-m", username])
            logging.info("User created successfully on Linux.")

            logging.info("Setting user password...")
            run_sudo_command(["chpasswd"])
            logging.info("Password set successfully.")

            logging.info("Forcing password change at first login (Linux)...")
            run_sudo_command(["chage", "-d", "0", username])
            logging.info("Password policy applied successfully.")

        else:
            error_msg = f"❌ Unsupported operating system: {system}"
            logging.error(error_msg)
            return error_msg

        success_msg = f"✅ User '{username}' created successfully. Default password is '{DEFAULT_PASSWORD}' and must be changed at first login."
        logging.info(success_msg)
        return success_msg

    except subprocess.CalledProcessError as e:
        error_msg = f"❌ Failed to create user '{username}'. Error: {e}"
        logging.error(error_msg)
        return error_msg


@mcp.tool()
def delete_user(username: str) -> str:
    """
    Delete an existing user on macOS or Ubuntu.

    Parameters:
    ----------
    username : str
        The username of the user to delete.

    Returns:
    -------
    str
        A message indicating whether the user was deleted successfully or an error occurred.
    """
    system = platform.system()

    logging.info(f"Detected OS: {system}")
    logging.info(f"Starting user deletion for '{username}'...")

    try:
        if system == "Darwin":  # macOS
            logging.info("Deleting user on macOS...")
            run_sudo_command(["sysadminctl", "-deleteUser", username])
            logging.info(f"User '{username}' deleted successfully from macOS.")

        elif system == "Linux":  # Ubuntu
            logging.info("Deleting user on Linux (Ubuntu)...")
            run_sudo_command(["deluser", "--remove-home", username])
            logging.info(f"User '{username}' deleted successfully from Linux.")

        else:
            error_msg = f"❌ Unsupported operating system: {system}"
            logging.error(error_msg)
            return error_msg

        success_msg = f"✅ User '{username}' deleted successfully."
        logging.info(success_msg)
        return success_msg

    except subprocess.CalledProcessError as e:
        error_msg = f"❌ Failed to delete user '{username}'. Error: {e}"
        logging.error(error_msg)
        return error_msg


if __name__ == "__main__":
    # Initialize and run the server
    logging.info("Starting FastMCP server...")
    mcp.run(transport="stdio")
