#!/usr/bin/env python
import os
import sys
import boto3
import json
import logging
import argparse
import configparser
from botocore.exceptions import ClientError

# Setting up logger
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s'
                    )
logger = logging.getLogger()


def get_aws_profile_arn(aws_config_file_path) -> dict:
    """
    :Description: To extract the profile name and corresponding role_arn
    from aws config file and return a dict
    :param aws_config_file_path: Path to the aws config file
    :return: A dict of profile's name and role_arn
    """
    profile_role_arn_dict = {}
    filename = os.path.expanduser(aws_config_file_path)

    if not os.path.exists(filename):
        logging.error(f"ERROR: {aws_config_file_path} file does not exist.")
        sys.exit(1)
    else:
        config = configparser.ConfigParser()
        config.read(filename)
        aws_profiles: list[str] = config.sections()

        if len(aws_profiles) == 0:
            logging.error(f"ERROR: {aws_config_file_path} file is empty.")
            sys.exit(1)

        for profile in aws_profiles:
            try:
                profile_role_arn_dict[profile] = config.get(profile, "role_arn")
            except configparser.NoOptionError:
                pass

    return profile_role_arn_dict


def choose_profile_option(profile_role_arn_dict: dict):
    """
    Description: To provide choice to user to select the profile from aws config
    and return a profile and corresponding arn
    :param profile_role_arn_dict: A dictionary of profile and role_arns
    :return: profile_name and role_arn
    """
    aws_profiles_list = []
    if profile_role_arn_dict:
        print("\nPlease choose from the following profile(s) : \n")
    else:
        logging.error("Config file has no role_arn")
        sys.exit(1)
    for k, v in profile_role_arn_dict.items():
        print(f"{list(profile_role_arn_dict).index(k) + 1})  {k}")
        aws_profiles_list.append(k)

    i = input("\n Enter profile id: ")

    if 0 < int(i) <= len(profile_role_arn_dict):
        profile_name = aws_profiles_list[int(i)-1]
        role_arn = profile_role_arn_dict[profile_name]
    else:
        logging.error("Please select correct profile id")
        sys.exit(1)

    return profile_name.split()[-1], role_arn


def get_credentials_for_role(selected_aws_profile, role_arn):
    """
    Description: Generate sts credentials for corresponding role
    :param selected_aws_profile: aws_profile name
    :param role_arn: role_arn
    :return: temporary session name and credentials object
    """
    session_name = f"temp_{selected_aws_profile}"
    session = boto3.Session(profile_name=selected_aws_profile)
    sts = session.client('sts')
    try:
        response = sts.assume_role(RoleArn=role_arn,
                                   RoleSessionName=session_name
                                   )
        return session_name, response['Credentials']
    except ClientError as e:
        logging.error(e.response['Error']['Message'])
        sys.exit(1)


def write_credentials(profile, credentials):
    """
    :param profile: Temporary session profile name
    :param credentials: sts crdential object
    :return: Write temporary credentials into ~/.aws/credentials file
    """
    filename = os.path.expanduser('~/.aws/credentials')
    dirname = os.path.dirname(filename)

    if not os.path.exists(dirname):
        os.makedirs(dirname)

    config = configparser.ConfigParser()
    config.read(filename)
    if not config.has_section(profile):
        config.add_section(profile)
    config.set(profile, 'aws_access_key_id', credentials['AccessKeyId'])
    config.set(profile, 'aws_secret_access_key', credentials['SecretAccessKey'])
    config.set(profile, 'aws_session_token', credentials['SessionToken'])
    try:
        with open(filename, 'w') as fp:
            config.write(fp)
        logging.info(f"Set your profile to {profile}, export AWS_PROFILE={profile} \n")
    except IOError:
        logging.error(f"Unable to write into {filename}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", "-o", required=False,
                        dest="output", help="Output format write or json, default='write'", metavar="STRING",
                        default="write", choices=['json', 'write'])
    parser.add_argument("--config-file", "-t", required=False,
                        dest="config_file", help="AWS config file path, default='~/.aws/config'", metavar="STRING",
                        default="~/.aws/config")

    options = parser.parse_args()

    aws_profiles = get_aws_profile_arn(options.config_file)
    selected_aws_profile, role_arn = choose_profile_option(aws_profiles)
    session_name, credentials = get_credentials_for_role(selected_aws_profile, role_arn)

    if options.output == 'write':
        write_credentials(session_name, credentials)
    elif options.output == 'json':
        print(json.dumps({'AWS_ACCESS_KEY_ID': credentials['AccessKeyId'],
                          'AWS_SECRET_ACCESS_KEY': credentials['SecretAccessKey'],
                          'AWS_SESSION_TOKEN': credentials['SessionToken']}))
