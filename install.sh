#!/bin/bash
# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

# shellcheck disable=SC1091,SC2181

# SDK is always installed in a directory in SDK_INSTALL_HOME.
# SDK_INSTALL_HOME is the user's HOME directory in a live install.
# SDK_INSTALL_HOME is a temporary directory in a test install.
#
# By default, we install files in directory qradarappsdk under SDK_INSTALL_HOME,
# so the full path is $SDK_INSTALL_HOME/qradarappsdk.
# The user can choose a different directory under SDK_INSTALL_HOME.
#
# The file $SDK_INSTALL_HOME/.qradar_app_sdk/install_dir identifies where the SDK is installed.
# It holds the path of the install directory relative to SDK_INSTALL_HOME, e.g.
#   qradarappsdk or
#   mystuff/qradar/sdk

source ./shinclude/install-config.sh
source ./shinclude/functions-python.sh
source ./shinclude/functions-util.sh

sdk_installer_dir=$(dirname "$0")

check_python_version()
{
    sdk_python_script=python3
    version_message="This SDK requires Python 3.6.8 or greater"
    python_version_output=$(retrieve_python3_version)

    if [ $? -ne 0 ]
    then
        python_version_output=$(retrieve_python_version)

        if [ $? -ne 0 ]
        then
            echo "$version_message"
            exit 1
        fi

        sdk_python_script=python
    fi

    python_version=$(echo "$python_version_output" | awk '{print $2}')

    IFS='.' read -r major minor patch<<<"$python_version"
    patch=${patch:-0}

    if [ "$major" -eq "3" ] && { [ "$minor" -gt "6" ] || { [ "$minor" -eq "6" ] && [ "$patch" -ge "8" ]; }; }
    then
        echo "Using Python $python_version"
    else
        echo "Found Python $python_version"
        echo "$version_message"
        exit 1
    fi
}

prepare_install_directory()
{
    old_location_holder="$SDK_INSTALL_HOME"/.qradar_app_sdk_dir
    new_location_holder="$SDK_INSTALL_HOME"/.qradar_app_sdk/install_dir
    sdk_location_holder="$new_location_holder"

    if [ -f "$old_location_holder" ]
    then
        sdk_location_holder="$old_location_holder"
    fi

    install_dir_default=qradarappsdk

    if [ -f "$sdk_location_holder" ]
    then
        location_file_content=$(xargs < "$sdk_location_holder")

        if [ ${#location_file_content} -gt 0 ]
        then
            validated_location=$(validate_install_location "$location_file_content")

            if [ ${#validated_location} -gt 0 ]
            then
                install_dir_default="$validated_location"
            fi
        fi
    fi

    echo "The SDK will be installed in your HOME directory"

    while true
    do
        install_dir=$install_dir_default

        echo "The default install location under your HOME directory is $install_dir_default"
        read -r -p "Press Enter to accept this location, or enter a new location: " input_dir

        if [ ${#input_dir} -gt 0 ]
        then
            validated_location=$(validate_install_location "$input_dir")

            if [ ${#validated_location} -gt 0 ]
            then
                install_dir="$validated_location"
            else
                echo "Directory $input_dir is not allowed. Please try again."
                echo "Install location must start with a letter or digit, followed by any of: a-z A-Z 0-9 . _ - /"
                continue
            fi
        fi

        sdk_install_path="$SDK_INSTALL_HOME"/"$install_dir"

        if [ -d "$sdk_install_path" ]
        then
            if [ ! -w "$sdk_install_path" ] || [ ! -x "$sdk_install_path" ]
            then
                echo "You do not have permission to install files in $sdk_install_path. Please try again."
                continue
            fi

            if not_empty "$sdk_install_path"
            then
                echo "Chosen install location $sdk_install_path is not empty"
                echo "The directory will be removed and recreated by this install script"
                read -r -p "Do you wish to continue? [y/n]: " response

                case $response in
                    [yY])
                        echo "Removing local install directory $sdk_install_path"
                        rm -rf "$sdk_install_path"

                        if [ -d "$sdk_install_path" ] && not_empty "$sdk_install_path"
                        then
                            echo "Unable to remove local install directory $sdk_install_path"
                            echo "Terminating install"
                            exit 1
                        fi
                        ;;
                    *)
                        echo "Terminating install"
                        exit 1
                        ;;
                esac
            fi
        fi

        break
    done

    # Quietly remove the old location holder file, no longer needed.
    rm -f "$old_location_holder"
    mkdir -p "$SDK_INSTALL_HOME"/.qradar_app_sdk
    echo "$install_dir" > "$new_location_holder"
    mkdir -p "$sdk_install_path"

    # This exit point allows tests to finish at the end of the information-gathering
    # phase and before files and python packages are installed.
    if [ -n "$SDK_TEST_INSTALL" ]
    then
        echo "Exiting test install"
        exit 0
    fi
}

install_sdk_files()
{
    echo "Copying files to $sdk_install_path"

    for i in base_image conf docs image_files lib template version.txt
    do
        cp -r "$sdk_installer_dir"/$i "$sdk_install_path" 2>/dev/null
    done

    # sdk-python-requirements.txt is only used by this install script and
    # is not needed under the installed SDK.
    rm -f "$sdk_install_path"/conf/sdk-python-requirements.txt

    mkdir "$sdk_install_path"/docker

    echo "Installing qapp in $SDK_BIN_DIR"

    if [ -w "$SDK_BIN_DIR" ]
    then
        cp -f "$sdk_installer_dir"/scripts/qapp "$SDK_BIN_DIR"
        chmod +x "$SDK_BIN_DIR"/qapp
    else
        echo "Acquiring elevated privileges for writing to $SDK_BIN_DIR"
        sudo -p "Please enter your system password: " cp -f "$sdk_installer_dir"/scripts/qapp "$SDK_BIN_DIR"
        sudo chmod +x "$SDK_BIN_DIR"/qapp
    fi
}

create_python_venv()
{
    echo "Creating Python virtual environment in $sdk_install_path/env"
    $sdk_python_script -m venv "$sdk_install_path"/env

    echo "Installing Python dependencies in virtual environment"
    "$sdk_install_path"/env/bin/python -m pip install --upgrade pip

    if [ $? -ne 0 ]
    then
		echo "Failed to upgrade pip. Terminating install"
		exit 1
    fi

    "$sdk_install_path"/env/bin/python -m pip install -r "$sdk_installer_dir"/conf/sdk-python-requirements.txt

    if [ $? -ne 0 ]
    then
        echo "Failed to install Python packages. Terminating install"
        exit 1
    fi
}

open_readme()
{
    sdk_readme="$sdk_install_path"/docs/qradar-app-sdk.html

    if [ -f "$sdk_readme" ]
    then
        read -r -p "View documentation? [y/n]: " response

        case $response in
            [yY])
                if which xdg-open &>/dev/null
                then
                    xdg-open "$sdk_readme" &>/dev/null &
                else
                    open "$sdk_readme" &>/dev/null &
                fi
                ;;
            *)
                ;;
        esac
    fi
}

echo "Starting QRadar App SDK install"

check_python_version
prepare_install_directory
install_sdk_files
create_python_venv
open_readme

echo "QRadar App SDK install completed"

