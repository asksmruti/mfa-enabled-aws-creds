
# AWS - cross account access using MFA 


Multi-factor authentication(MFA) or two-factor authentication (2FA), is highly recommended for keeping the AWS accounts safe as it provides an additional layer of security for the user accounts.
However this comes with little complexity for the developers to perform a day-to-day job. 
This repository is all about how to tackle those challenges in several ways.

In the large organisations, usually the users will be provided access to MFA enabled centralized AWS account(with very minimum access).
That is kinda gateway to login to another account by switching the role.

### AWS config file


The MFA can be configured through AWS config and credentials file like below.
It will allow the user to run aws cli by setting up the right profile.

Here is one example of credentials and config files -

Set the primary account credentials in the `~/.aws/credentials` file
```shell
[main]  ## This is the main or primary account
aws_access_key_id = xxxxxx
aws_secret_access_key = xxxxxxx
```

All the secondary accounts will be in the `~/.aws/config` file.
```shell
[profile main]
region = us-central-1

[profile dev-1]
region = eu-central-1
role_arn = arn:aws:iam::<dev-1 account ID>:role/<dev-1 account role_name> ## The role to be assumed
source_profile = main
mfa_serial = arn:aws:iam::<main account ID>:mfa/<main account user name>

[profile dev-2]
region = eu-west-1
role_arn = arn:aws:iam::<dev-2 account ID>:role/<dev-2 account role_name>
source_profile = main
mfa_serial = arn:aws:iam::<main account ID>:mfa/<main account user name>
```
Now, the AWS profile can be set to get access to corresponding AWS account.

```shell
$ export AWS_PROFILE=dev-1
$ aws s3 ls
Enter MFA code for arn:aws:iam::<main account ID>:mfa/<main account user name>: 

```

### aws-vault 


Probably, it would be tedious and may be some difficulties while setting up the profile every time or pass the profile argument to each command.
In those scenarios, `aws-vault plays` a nice role. 

More details for aws vault can be found here - https://github.com/99designs/aws-vault

Basically, the main/primary(MFA) account will be added to aws-vault.

```shell
$ aws-vault add main
```
Then, for all other accounts, the alias can be created and set it in `~/.profile` file.

```
# Setup AWS
# alias <your_favorite_name>="aws-vault exec <aws_profile_name> -- "
alias aws-dev-1="aws-vault exec dev-1 -- " 
alias aws-dev-2="aws-vault exec dev-2 -- "
```
Afterwards, these aliases can be used to trigger the commands to communicate with corresponding AWS account.
Here is one example - 

```shell
$ aws-dev-1 aws s3 ls
Enter MFA code for arn:aws:iam::<main account ID>:mfa/<main account user name>: 
<< This will connect to AWS account -1 >> 

$ aws-dev-2 terraform init
Enter MFA code for arn:aws:iam::<main account ID>:mfa/<main account user name>: 
<< This will connect to AWS account -2 >> 
```

### aws_mfa_ca_credentials.py


The above two approach will solve almost all hurdles.
However, in both scenarios, it will not provide you the temporary credentials as such, which you may need.

The MFA enabled cross account - generate credential utility can be helpful, to retrieve the temporary token or credentials.
It will write the credentials into `~/.aws/credentials` file or return the credentials on standard output.

```shell
$ python3 aws_mfa_ca_credentials.py --help

usage: aws_mfa_ca_credentials.py [-h] [--output STRING] [--config-file STRING]

optional arguments:
  -h, --help            show this help message and exit
  --output STRING, -o STRING
                        Output format write or json, default='write'
  --config-file STRING, -t STRING
                        AWS config file path, default='~/.aws/config'

```
It reads the `~/.aws/config` file, generate or write the credentials into `~/.aws/credentials` file.

```shell
$ python3 aws_mfa_ca_credentials.py 

Please choose from the following profile(s) : 

1)  profile dev-1
2)  profile dev-2
3)  profile dev-3

 Enter profile id: 2
2021-07-08 13:12:27,017 INFO: Found credentials in shared credentials file: ~/.aws/credentials
Enter MFA code for arn:aws:iam::<main account ID>:mfa/<main account user name>: 
2021-07-08 13:12:51,698 INFO: Set your profile to temp_default, export AWS_PROFILE=temp_dev-2

```

If the output set to `json` then it'll return the credentials on standard output.






