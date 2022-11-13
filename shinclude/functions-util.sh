# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

validate_install_location()
{
    location=$1

    # Start with letter or digit, then letters, digits, dot, underscore, slash, dash.
    # Do not allow path traversal.
    if [[ ! "$location" =~ ^[0-9A-Za-z][0-9A-Za-z._\/-]*$ ]] || [[ "$location" =~ \.\. ]]
    then
        echo ""
    else
        # Remove repeated slashes
        location=$(echo "$location" | tr -s /)

        # Strip trailing slash.
        dir_separator="/"
        location=${location%$dir_separator}

        echo "$location"
    fi
}

not_empty()
{
    # This find command produces output ONLY IF the supplied directory is empty.
    # Therefore we check for an empty string - this means the directory is not empty.
    [ -z "$(find "$1" -maxdepth 0 -type d -empty 2>/dev/null)" ]
}
