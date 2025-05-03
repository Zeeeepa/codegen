from codegen.cli.env.enums import Environment
from codegen.cli.env.global_env import global_env


def get_modal_workspace():
    # Replace match statement with if-elif for compatibility
    if global_env.ENV == Environment.PRODUCTION:
        return "codegen-sh"
    elif global_env.ENV == Environment.STAGING:
        return "codegen-sh-staging"
    elif global_env.ENV == Environment.DEVELOP:
        return "codegen-sh-dev"
    else:
        msg = f"Invalid environment: {global_env.ENV}"
        raise ValueError(msg)


def get_modal_prefix():
    workspace = get_modal_workspace()
    if global_env.ENV == Environment.DEVELOP and global_env.MODAL_ENVIRONMENT:
        return f"{workspace}-{global_env.MODAL_ENVIRONMENT}"
    return workspace


MODAL_PREFIX = get_modal_prefix()
