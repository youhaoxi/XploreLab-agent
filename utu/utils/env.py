from dotenv import load_dotenv, find_dotenv

def setup_env():
    load_dotenv(find_dotenv(raise_error_if_not_found=True), verbose=True, override=True)
