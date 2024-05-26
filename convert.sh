#! /bin/sh

set -ex
# Define the source and destination directories
SOURCE_DIR="/home/dima/Code/OpenSSL/openssl-fork/doc"
DEST_DIR="/home/dima/Code/OpenSSL/openssl-docs/docs"

# Find all .pod files and process them
find "$SOURCE_DIR" -type f -name "*.pod" | while read -r podfile; do
  # Create the corresponding .md filename
  mdfile="${podfile%.pod}.md"

  # Convert the .pod file to .md using pod2md
  /home/dima/perl5/bin/pod2markdown --man-url-prefix "../../man" "$podfile" > "$mdfile"

  # Create the destination directory if it doesn't exist
  destfile="$DEST_DIR/${mdfile#$SOURCE_DIR/}"
  mkdir -p "$(dirname "$destfile")"

  # Copy the .md file to the destination directory
  mv "$mdfile" "$destfile"
done
