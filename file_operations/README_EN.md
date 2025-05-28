<p align="center">
  <a href="./README_EN.md">English</a> |
  <a href="./README.md">简体中文</a> 
</p>

----

# File Operation Scripts

This directory contains practical scripts for file operations.

## organize_files.py - File Organization Tool

This script can help you automatically organize messy folders by categorizing files into different subfolders by type.

### Features

- Supports automatic classification of various common file types (images, documents, audio, video, etc.)
- Generates detailed organization reports
- Option to only generate reports without moving files
- Supports excluding specified directories
- Option to process hidden files

### Usage

Basic usage (organize current directory):
```bash
python organize_files.py
```

Organize a specific directory:
```bash
python organize_files.py D:\Downloads
```

Generate report only without moving files:
```bash
python organize_files.py -r
```

Exclude certain directories:
```bash
python organize_files.py -e Images Documents
```

Include hidden files:
```bash
python organize_files.py --include-hidden
```

### Complete Command Line Parameters

```
usage: organize_files.py [-h] [-r] [-e EXCLUDE [EXCLUDE ...]] [--include-hidden] [directory]

File Organization Tool - Organize files by type

positional arguments:
  directory             Directory path to organize, default is current directory

options:
  -h, --help            Show help information and exit
  -r, --report-only     Generate report only, don't move files
  -e EXCLUDE [EXCLUDE ...], --exclude EXCLUDE [EXCLUDE ...]
                        List of directory names to exclude
  --include-hidden      Include hidden files
```

## batch_rename.py - Batch File Renaming Tool

This script provides multiple ways to batch rename files, supporting various renaming modes, file filtering, preview, and undo functionality.

### Features

- **Multiple Renaming Modes**:
  - Add prefix/suffix
  - Add sequence number
  - Add date/time (file modification time or current time)
  - Regular expression replacement
  - Change filename case
  - Replace spaces with specified characters
- **Advanced File Filtering**:
  - Filter by file extension
  - Filter by file size range
  - Exclude files using regular expressions
- **Safe Operations**:
  - Preview renaming effects
  - Detect and prompt for naming conflicts
  - Automatically back up overwritten files
- **Operation History**:
  - Save rename operation history
  - Support undoing previous rename operations

### Basic Usage

Add prefix:
```bash
python batch_rename.py --add-prefix "New_" 
```

Add suffix (before extension):
```bash
python batch_rename.py --add-suffix "_edited" --before-ext
```

Add sequence number:
```bash
python batch_rename.py --add-sequence --start-num 1 --padding 3
```

Rename by modification date:
```bash
python batch_rename.py --add-date --use-file-time
```

Regular expression replacement:
```bash
python batch_rename.py --replace "(\d+)" "num_$1"
```

Change filename case:
```bash
python batch_rename.py --change-case upper
```

Replace spaces in filenames:
```bash
python batch_rename.py --replace-spaces "_"
```

### Advanced Usage Examples

Process only specific extensions:
```bash
python batch_rename.py --add-prefix "Image_" -e jpg png gif
```

Recursively process subdirectories:
```bash
python batch_rename.py --add-date -r
```

Preview without actually renaming:
```bash
python batch_rename.py --add-sequence --dry-run
```

Filter files by size range:
```bash
python batch_rename.py --add-prefix "Large_" --min-size 1048576
```

View historical rename operations:
```bash
python batch_rename.py --list-history
```

Undo a previous rename operation:
```bash
python batch_rename.py --undo 1
```

### Complete Command Line Parameters

```
usage: batch_rename.py [-h] [-r] [--dry-run] [-e EXTENSIONS [EXTENSIONS ...]]
                      [--min-size MIN_SIZE] [--max-size MAX_SIZE]
                      [--exclude EXCLUDE] [--add-prefix PREFIX | --add-suffix SUFFIX |
                      --add-sequence | --add-date | --replace PATTERN REPLACEMENT |
                      --change-case {upper,lower,title,capitalize} |
                      --replace-spaces [CHAR] | --list-history | --undo ID]
                      [--before-ext] [--start-num START_NUM]
                      [--padding PADDING] [--seq-position {prefix,suffix}]
                      [--date-format DATE_FORMAT] [--use-file-time]
                      [--date-position {prefix,suffix}]
                      [directory]

Batch File Renaming Tool

positional arguments:
  directory             Directory path to process, default is current directory

options:
  -h, --help            Show help information and exit
  -r, --recursive       Process subdirectories recursively
  --dry-run             Simulate run, don't actually rename files

File filtering options:
  -e, --extensions EXTENSIONS [EXTENSIONS ...]
                        List of file extensions to process, such as '.jpg .png'
  --min-size MIN_SIZE   Minimum file size (bytes)
  --max-size MAX_SIZE   Maximum file size (bytes)
  --exclude EXCLUDE     Excluded filename pattern (regular expression)

Renaming operations (choose only one):
  --add-prefix PREFIX   Add prefix
  --add-suffix SUFFIX   Add suffix
  --before-ext          Add suffix before extension, used with --add-suffix
  --add-sequence        Add sequence number
  --start-num START_NUM Sequence number start value
  --padding PADDING     Sequence number digits (zero padding)
  --seq-position {prefix,suffix}
                        Sequence number position, prefix or suffix
  --add-date            Add date/time
  --date-format DATE_FORMAT
                        Date/time format
  --use-file-time       Use file modification time (otherwise use current time)
  --date-position {prefix,suffix}
                        Date position, prefix or suffix
  --replace PATTERN REPLACEMENT
                        Replace content in filenames (using regular expressions)
  --change-case {upper,lower,title,capitalize}
                        Change filename case
  --replace-spaces [CHAR]
                        Replace spaces in filenames (default: replace with underscore)
  --list-history        Display historical rename records
  --undo ID             Undo specified rename operation (use --list-history to see available IDs)
```

## file_finder.py - File Search Tool

This script provides powerful file search functionality, supporting searches by multiple criteria, and can sort and format the results.

### Features

- **Multiple Search Criteria**:
  - Search by filename (supports wildcards and regular expressions)
  - Search by file extension
  - Search by file size range
  - Search by file date range (modified date, created date, accessed date)
  - Search by file content (supports text patterns and regular expressions)
- **Advanced Filtering**:
  - Include/exclude hidden files
  - Filter for files or directories only
  - Limit result count
- **Result Processing**:
  - Multiple sorting methods (name, size, date, extension, path)
  - Multiple output formats (list, table, CSV)
  - Display content match lines (with context)
  - Save results to file

### Basic Usage

Search by filename (supports wildcards):
```bash
python file_finder.py -n "*.txt"
```

Search by file extension:
```bash
python file_finder.py -e jpg png gif
```

Search by file content:
```bash
python file_finder.py -c "search text"
```

## file_compare.py - File and Directory Comparison Tool

This script provides powerful file and directory comparison functionality, can identify and display differences between files, as well as compare directory structures and contents.

### Features

- **File Comparison**:
  - Supports line-level comparison of text files
  - Supports binary file comparison
  - Option to ignore whitespace, case, and blank lines
  - Displays context differences
  - Comparison methods optimized for large files
- **Directory Comparison**:
  - Identifies files and directories that exist only on one side
  - Compares contents of files that exist on both sides
  - Recursively compares subdirectories
  - Supports ignoring specific files or directories
- **Difference Reports**:
  - Text format reports (console friendly)
  - HTML format reports (with color highlighting)
  - JSON format reports (for programmatic processing)
  - Option to save reports to a file

### Basic Usage

Compare two files:
```bash
python file_compare.py file1.txt file2.txt
```

Compare two directories:
```bash
python file_compare.py dir1 dir2
```

Generate HTML format report:
```bash
python file_compare.py file1.py file2.py --format html -o report.html
```

Ignore whitespace and case:
```bash
python file_compare.py file1.txt file2.txt -w -i
```

### Advanced Usage Examples

Ignore certain files when comparing directories:
```bash
python file_compare.py project1 project2 --ignore "*.pyc" "*.log" "__pycache__"
```

Only show summary information:
```bash
python file_compare.py dir1 dir2 -q
```

Show more context lines:
```bash
python file_compare.py file1.py file2.py --context-lines 5
```

Don't recursively compare subdirectories:
```bash
python file_compare.py dir1 dir2 --no-recursive
```

Generate JSON format report:
```bash
python file_compare.py dir1 dir2 --format json -o diff.json
```

### Complete Command Line Parameters

```
usage: file_compare.py [-h] [-r] [--no-recursive] [-i] [-w] [-B]
                      [-c CONTEXT_LINES] [--binary]
                      [--ignore IGNORE [IGNORE ...]]
                      [--format {text,html,json}] [-o OUTPUT] [-q] [-v]
                      path1 path2

File and Directory Comparison Tool

positional arguments:
  path1                 First file or directory path
  path2                 Second file or directory path

comparison options:
  -r, --recursive       Recursively compare subdirectories (enabled by default)
  --no-recursive        Don't recursively compare subdirectories
  -i, --ignore-case     Ignore case differences
  -w, --ignore-whitespace
                        Ignore whitespace differences
  -B, --ignore-blank-lines
                        Ignore blank lines
  -c, --context-lines CONTEXT_LINES
                        Number of context lines to show around differences (default: 3)
  --binary              Compare files in binary mode

filter options:
  --ignore IGNORE [IGNORE ...]
                        List of file or directory patterns to ignore (e.g., *.pyc __pycache__)

output options:
  --format {text,html,json}
                        Output format (default: text)
  -o, --output OUTPUT   Output report file path
  -q, --quiet           Quiet mode, only show summary information
  -v, --verbose         Verbose mode, show more information
```

## file_encrypt.py - File Encryption/Decryption Tool

This script provides file and directory encryption and decryption functionality for protecting sensitive data and personal privacy files.

### Features

- **Multiple Encryption Algorithms**:
  - AES (Advanced Encryption Standard) - Symmetric encryption algorithm widely used for data protection
  - Fernet - High-level encryption scheme from Python's cryptography library providing authenticated encryption
- **File Security Measures**:
  - Password-based encryption using PBKDF2 for key derivation
  - Randomly generated salt to enhance security
  - File integrity verification (SHA-256 hash)
  - Secure deletion option (overwrite original file contents multiple times)
- **Batch Processing**:
  - Support for encrypting/decrypting single files and entire directory trees
  - Recursive processing of subdirectories
  - Selective exclusion of specific files
- **User-Friendly Interface**:
  - Interactive password input (without displaying password)
  - Encryption/decryption progress feedback
  - Detailed error reporting

### Basic Usage

Encrypt a single file:
```bash
python file_encrypt.py -e sensitive_document.docx
```

Decrypt a file:
```bash
python file_encrypt.py -d sensitive_document.docx.encrypted
```

Encrypt an entire directory:
```bash
python file_encrypt.py -e important_folder
```

Decrypt an entire directory:
```bash
python file_encrypt.py -d important_folder_encrypted
```

Generate a random strong password:
```bash
python file_encrypt.py -g
```

### Advanced Usage Examples

Encrypt using AES algorithm:
```bash
python file_encrypt.py -e data.db -a aes
```

Specify output path:
```bash
python file_encrypt.py -e photos.zip -o "D:\Backup\photos.zip.encrypted"
```

Delete original file after encryption:
```bash
python file_encrypt.py -e tax_documents.pdf --delete
```

Exclude certain files:
```bash
python file_encrypt.py -e project_folder --exclude "*.log" "*.tmp" ".git*"
```

Read password from file (for script automation):
```bash
python file_encrypt.py -e database.sql --password-file my_password.txt
```

Don't recursively process subdirectories:
```bash
python file_encrypt.py -e data_folder --no-recursive
```

### Complete Command Line Parameters

```
usage: file_encrypt.py [-h] (-e | -d | -g) [-o OUTPUT] [-a {aes,fernet}]
                      [-p PASSWORD] [--password-file PASSWORD_FILE] [--delete]
                      [-r] [--no-recursive] [--exclude EXCLUDE [EXCLUDE ...]]
                      [--no-verify] [--length LENGTH] [-q] [-v]
                      [path]

File Encryption/Decryption Tool

positional arguments:
  path                  File or directory path to process

options:
  -h, --help            Show help information and exit
  -e, --encrypt         Encrypt file or directory
  -d, --decrypt         Decrypt file or directory
  -g, --generate-password
                        Generate a random password
  -o, --output OUTPUT   Output file or directory path
  -a, --algorithm {aes,fernet}
                        Encryption algorithm (default: fernet)
  -p, --password PASSWORD
                        Encryption/decryption password (not recommended to use on command line)
  --password-file PASSWORD_FILE
                        Read password from file
  --delete              Delete original file after processing
  -r, --recursive       Recursively process subdirectories (enabled by default)
  --no-recursive        Don't recursively process subdirectories
  --exclude EXCLUDE [EXCLUDE ...]
                        List of file patterns to exclude (e.g., *.log *.tmp)
  --no-verify           Don't verify file integrity during decryption
  --length LENGTH       Length of generated random password (default: 16)
  -q, --quiet           Quiet mode, reduce output
  -v, --verbose         Verbose mode, show more information
```

### Security Notes

- Please keep your password safe; once lost, encrypted files cannot be recovered
- Regular backups of important data are recommended
- Interactive password input is recommended to avoid providing passwords directly in command line
- Exercise extra caution when using the `--delete` option, as original files will be securely deleted and cannot be recovered

## file_sync.py - File Synchronization Tool

This script provides directory synchronization functionality that can maintain file content consistency between two directories, suitable for backing up data, synchronizing work files, and project collaboration.

### Features

- **Multiple Synchronization Modes**:
  - One-way sync (from source to target)
  - Two-way sync (mutual synchronization between two directories, keeping the newest files)
  - Mirror sync (make target directory exactly match source, including deleting files in target that don't exist in source)
  - Update mode (only update files already existing in target)
- **Intelligent File Comparison**:
  - Quick comparison based on modification time
  - Pre-filtering based on file size
  - Precise comparison based on content hash
- **Flexible Filtering Options**:
  - Option to exclude specific file patterns (e.g., *.tmp, *.log)
  - Option to include hidden files
  - Support for handling symbolic links
- **Conflict Resolution Strategies**:
  - Based on modification time (keep newer file)
  - Based on file size (keep larger file)
  - Fixed strategy (always use source or target file)
  - Option to skip conflicting files
- **Detailed Synchronization Reports**:
  - Statistics (number of copied, updated, deleted, skipped files)
  - File operation logs
  - Exportable in JSON format

### Basic Usage

One-way sync (default mode):
```bash
python file_sync.py source_dir target_dir
```

Two-way sync:
```bash
python file_sync.py source_dir target_dir -m two-way
```

Mirror sync:
```bash
python file_sync.py source_dir target_dir -m mirror
```

Update mode:
```bash
python file_sync.py source_dir target_dir -m update
```

### Advanced Usage Examples

Exclude specific files:
```bash
python file_sync.py source_dir target_dir -e "*.tmp" "*.log" ".git*"
```

Simulate run (doesn't actually modify files):
```bash
python file_sync.py source_dir target_dir --dry-run
```

Use specific conflict resolution strategy:
```bash
python file_sync.py source_dir target_dir -m two-way -c larger
```

Generate synchronization report:
```bash
python file_sync.py source_dir target_dir -r sync_report.json
```

Include hidden files and follow symbolic links:
```bash
python file_sync.py source_dir target_dir --include-hidden --follow-symlinks
```

Delete files in target directory that don't exist in source:
```bash
python file_sync.py source_dir target_dir --delete-orphaned
```

### Complete Command Line Parameters

```
usage: file_sync.py [-h] [-m {one-way,two-way,mirror,update}]
                   [-c {newer,larger,source,target,skip,prompt}]
                   [-e EXCLUDE [EXCLUDE ...]] [--include-hidden]
                   [--delete-orphaned] [--no-metadata] [--follow-symlinks]
                   [--dry-run] [-r REPORT] [-q] [-v]
                   source target

File Synchronization Tool - Synchronize content between two directories

positional arguments:
  source                Source directory path
  target                Target directory path

options:
  -h, --help            Show help information and exit
  -m, --mode {one-way,two-way,mirror,update}
                        Synchronization mode (default: one-way)
  -c, --conflict {newer,larger,source,target,skip,prompt}
                        Conflict resolution strategy (default: newer)
  -e, --exclude EXCLUDE [EXCLUDE ...]
                        List of file patterns to exclude (e.g., *.tmp *.log)
  --include-hidden      Include hidden files (starting with .)
  --delete-orphaned     Delete files in target that don't exist in source
  --no-metadata         Don't preserve file metadata (modification time, etc.)
  --follow-symlinks     Follow symbolic links
  --dry-run             Only simulate run, don't actually modify files
  -r, --report REPORT   File path for generating synchronization report
  -q, --quiet           Quiet mode, reduce output
  -v, --verbose         Verbose mode, show more information
```

### Synchronization Mode Explanation

- **One-way sync (one-way)**: Copies files from source directory to target directory. Only adds or updates files, doesn't delete any files in target directory.
- **Two-way sync (two-way)**: Mutual synchronization between two directories, preserving the newest file versions. Suitable for synchronizing files between two work environments.
- **Mirror sync (mirror)**: Makes target directory an exact replica of source directory, including deleting files in target that don't exist in source. Suitable for backup scenarios.
- **Update mode (update)**: Only updates files already existing in target directory, doesn't add new files or delete files. Suitable for updating already deployed applications.

### Conflict Resolution Strategies

When doing two-way synchronization, if the same file has been modified in both directories, a conflict occurs. This can be resolved using the following strategies:

- **newer**: Keep the file with the most recent modification time (default)
- **larger**: Keep the file with the larger size
- **source**: Always use the file from source directory
- **target**: Always use the file from target directory
- **skip**: Skip conflicting files, don't synchronize them
- **prompt**: Prompt the user to choose (currently not implemented, equivalent to skip) 

## file_compress.py - File Compression and Extraction Tool

This script provides file compression and extraction functionality, supporting multiple compression formats.

### Features

- **Multiple Compression Format Support**:
  - ZIP format (.zip)
  - TAR format (.tar)
  - TAR with GZIP compression (.tar.gz, .tgz)
  - TAR with BZIP2 compression (.tar.bz2, .tbz2)
- **Flexible Compression Options**:
  - Compression level control (tradeoff between speed and size)
  - Password protection (for ZIP format)
  - Comment addition to archives
  - Split large archives into multiple parts
- **Directory Compression**:
  - Recursively compress entire directory trees
  - Option to preserve directory structure
  - Selective inclusion/exclusion of files by pattern
- **Extraction Capabilities**:
  - Full archive extraction
  - Extract specific files only
  - Control destination path for extracted files
  - Preview archive contents without extracting
- **Archive Management**:
  - List archive contents
  - Test archive integrity
  - Add, delete or update files in existing archives

### Basic Usage

Compress a file:
```bash
python file_compress.py -c file.txt
```

Compress multiple files into an archive:
```bash
python file_compress.py -c file1.txt file2.jpg file3.pdf -o archive.zip
```

Compress a directory:
```bash
python file_compress.py -c my_folder -o my_archive.zip
```

Extract an archive:
```bash
python file_compress.py -x archive.zip
```

List archive contents:
```bash
python file_compress.py -l archive.zip
```

### Advanced Usage Examples

Specify compression format (tar.gz):
```bash
python file_compress.py -c source_code -o backup.tar.gz -f tgz
```

Set compression level (1-9, where 9 is maximum compression):
```bash
python file_compress.py -c large_files -o compressed.zip --level 9
```

Password protect a ZIP archive:
```bash
python file_compress.py -c confidential_docs -o secure.zip --password
```

Extract to specific directory:
```bash
python file_compress.py -x archive.zip -d C:\extracted_files
```

Extract specific files only:
```bash
python file_compress.py -x archive.zip --files "*.jpg" "docs/*.txt"
```

Exclude certain file patterns from compression:
```bash
python file_compress.py -c project_folder -o project.zip --exclude "*.log" "*.tmp" ".git/*"
```

Add files to existing archive:
```bash
python file_compress.py -a archive.zip -f new_file.txt another_file.jpg
```

Split large archive into multiple parts:
```bash
python file_compress.py -c huge_folder -o backup.zip --split-size 100M
```

### Complete Command Line Parameters

```
usage: file_compress.py [-h] (-c | -x | -l | -t | -a | -u | -d)
                       [-o OUTPUT] [-f {zip,tar,tgz,tbz2}] [--level LEVEL]
                       [--password] [--comment COMMENT] [-d DESTINATION]
                       [--files [FILES ...]] [--exclude [EXCLUDE ...]]
                       [--include-hidden] [--split-size SPLIT_SIZE]
                       [--preserve-symlinks] [-r] [--no-recursive] [-q] [-v]
                       [paths ...]

File Compression and Extraction Tool

positional arguments:
  paths                 Files or directories to process

operation options:
  -h, --help            Show help information and exit
  -c, --compress        Compress files or directories
  -x, --extract         Extract an archive
  -l, --list            List archive contents
  -t, --test            Test archive integrity
  -a, --add             Add files to existing archive
  -u, --update          Update files in existing archive
  -d, --delete          Delete files from existing archive

compression options:
  -o, --output OUTPUT   Output file path
  -f, --format {zip,tar,tgz,tbz2}
                        Compression format (default: zip)
  --level LEVEL         Compression level 1-9 (default: 6)
  --password            Password protect the archive (only for ZIP)
  --comment COMMENT     Add comment to the archive

extraction options:
  -d, --destination DESTINATION
                        Destination directory for extracted files
  --files [FILES ...]   Specific files to extract (supports wildcards)

filter options:
  --exclude [EXCLUDE ...]
                        Exclude file patterns (e.g., *.tmp, *.log)
  --include-hidden      Include hidden files and directories
  --split-size SPLIT_SIZE
                        Split archive into multiple parts (format: nM or nG)
  --preserve-symlinks   Preserve symbolic links in archive
  -r, --recursive       Process directories recursively (default)
  --no-recursive        Don't process directories recursively
  -q, --quiet           Quiet mode, reduce output
  -v, --verbose         Verbose mode, show more information
```

### Notes

- Password protection is only available for ZIP format
- For very large directories, higher compression levels may take significantly longer
- When compressing sensitive data, consider using file_encrypt.py for additional security
- Split archives can only be created in ZIP format
- For maximum compatibility across platforms, use ZIP format

## file_dupes.py - Duplicate File Finder

This script helps identify and manage duplicate files across directories, saving disk space by finding and removing unnecessary duplicates.

### Features

- **Multiple File Comparison Methods**:
  - Fast comparison by file size
  - Content-based comparison using hash algorithms (MD5, SHA-1, SHA-256)
  - Byte-by-byte comparison for exact verification
  - Option for fuzzy matching of image files (similar but not identical images)
- **Extensive Search Capabilities**:
  - Recursive directory scanning
  - Flexible file filtering by patterns, size ranges, and date ranges
  - Option to include/exclude hidden files and system files
- **Duplicate Processing Options**:
  - Interactive deletion prompts
  - Automatic deletion (keeping first, newest, or largest file)
  - Move duplicates to separate folder
  - Replace duplicates with symbolic links (save space while keeping file structure)
  - Generate detailed reports in various formats (text, CSV, JSON)
- **Advanced Features**:
  - Comparing files across multiple directories
  - Checksums caching for faster re-scans
  - Preview content of matched files
  - Dry run mode to simulate actions

### Basic Usage

Find duplicates in a directory:
```bash
python file_dupes.py C:\Photos
```

Find duplicates across multiple directories:
```bash
python file_dupes.py C:\Photos D:\Backup\Photos E:\Media\Images
```

Generate a report without deleting anything:
```bash
python file_dupes.py C:\Data --report duplicate_report.txt
```

### Advanced Usage Examples

Find duplicates using a specific hash algorithm:
```bash
python file_dupes.py Documents/ --hash sha256
```

Find only image file duplicates:
```bash
python file_dupes.py Media/ --include "*.jpg" "*.png" "*.gif" "*.bmp"
```

Find duplicates and interact with each group:
```bash
python file_dupes.py Downloads/ --interactive
```

Find duplicates and automatically delete them (keeping first occurrence):
```bash
python file_dupes.py Downloads/ --delete first
```

Move duplicates to another folder:
```bash
python file_dupes.py Projects/ --move-to D:\Duplicates
```

Find large duplicates (>10MB):
```bash
python file_dupes.py D:\ --min-size 10M
```

Replace duplicates with symbolic links:
```bash
python file_dupes.py Media/ --symlink
```

Check for duplicates against a reference directory (don't find duplicates within reference):
```bash
python file_dupes.py NewPhotos/ --reference-dir OriginalPhotos/
```

Find image files that look similar (not just exact duplicates):
```bash
python file_dupes.py Pictures/ --fuzzy-match --similarity 90
```

### Complete Command Line Parameters

```
usage: file_dupes.py [-h] [--hash {md5,sha1,sha256,xxhash}]
                    [--min-size MIN_SIZE] [--max-size MAX_SIZE]
                    [--include [INCLUDE ...]] [--exclude [EXCLUDE ...]]
                    [--exclude-dir [EXCLUDE_DIR ...]] [--interactive]
                    [--delete {first,newest,oldest,largest,smallest}]
                    [--move-to MOVE_TO] [--symlink] [--report REPORT]
                    [--format {text,csv,json}] [--dry-run] [--no-recursive]
                    [--include-hidden] [--include-system] [--reference-dir REFERENCE_DIR]
                    [--fuzzy-match] [--similarity SIMILARITY] [--cache-file CACHE_FILE]
                    [--preserve-cache] [-q] [-v]
                    directories [directories ...]

Duplicate File Finder - Find and manage duplicate files to save disk space

positional arguments:
  directories           Directories to scan for duplicates

options:
  -h, --help            Show help information and exit
  --hash {md5,sha1,sha256,xxhash}
                        Hash algorithm to use for file comparison (default: md5)
  --min-size MIN_SIZE   Minimum file size to consider (format: n[K|M|G])
  --max-size MAX_SIZE   Maximum file size to consider (format: n[K|M|G])
  --include [INCLUDE ...]
                        File patterns to include (e.g., "*.jpg" "*.pdf")
  --exclude [EXCLUDE ...]
                        File patterns to exclude (e.g., "*.tmp" "*.log")
  --exclude-dir [EXCLUDE_DIR ...]
                        Directories to exclude from scan
  --interactive         Interactive mode - prompt for action on each duplicate group
  --delete {first,newest,oldest,largest,smallest}
                        Automatically delete duplicates, keeping the specified file
  --move-to MOVE_TO     Move duplicate files to this directory
  --symlink             Replace duplicates with symbolic links to save space
  --report REPORT       Generate a report file with duplicate information
  --format {text,csv,json}
                        Format for report output (default: text)
  --dry-run             Simulation mode - don't actually delete or move files
  --no-recursive        Don't recursively scan directories
  --include-hidden      Include hidden files (starting with .)
  --include-system      Include system files
  --reference-dir REFERENCE_DIR
                        Compare against this reference directory without finding duplicates within it
  --fuzzy-match         Enable fuzzy matching for image files (similar but not identical)
  --similarity SIMILARITY
                        Similarity threshold % for fuzzy matching (default: 95)
  --cache-file CACHE_FILE
                        File to store/load checksums cache
  --preserve-cache      Preserve cache even when scan parameters change
  -q, --quiet           Quiet mode, reduce output
  -v, --verbose         Verbose mode, show more information
```

### Notes on Deletion

Be extremely cautious when using automatic deletion options. The tool works as follows:

- `--delete first`: Keeps the first occurrence of each file (by directory order)
- `--delete newest`: Keeps the most recently modified file in each duplicate group
- `--delete oldest`: Keeps the oldest file in each duplicate group
- `--delete largest`: Keeps the largest file in case of byte count differences
- `--delete smallest`: Keeps the smallest file in case of byte count differences

Always consider running with `--dry-run` first to see what would be deleted.

## file_monitor.py - File System Change Monitor

This script provides real-time monitoring of file system changes in specified directories, detecting file creation, modification, deletion, and renaming events.

### Features

- **Real-time Monitoring**:
  - Detects file creation events
  - Detects file modification events
  - Detects file deletion events
  - Detects file renaming events
  - Detects directory creation/deletion events
- **Flexible Event Filtering**:
  - Monitor specific event types
  - Include/exclude files based on patterns
  - Control recursion into subdirectories
  - Option to ignore temporary editor files
- **Action Triggers**:
  - Log all events with timestamps
  - Execute custom commands on specific events
  - Copy changed files to a backup location
  - Send notifications when important changes occur
- **Advanced Options**:
  - Latency control to handle burst events
  - Batch event processing
  - Daemon mode for continuous background monitoring
  - Detailed logging with various verbosity levels

### Basic Usage

Monitor a directory for all changes:
```bash
python file_monitor.py watch D:\Projects\MyWebsite
```

Run the monitor as a background process:
```bash
python file_monitor.py watch D:\Projects\MyWebsite --daemon
```

Show currently active monitors:
```bash
python file_monitor.py status
```

Stop a running monitor:
```bash
python file_monitor.py stop <monitor_id>
```

### Advanced Usage Examples

Monitor only specific events:
```bash
python file_monitor.py watch D:\Projects\MyWebsite --events create modify
```

Monitor with file pattern filters:
```bash
python file_monitor.py watch D:\Projects\MyWebsite --include "*.html" "*.css" "*.js" --exclude "*.tmp" "*.log"
```

Execute a command when files change (backup changed files):
```bash
python file_monitor.py watch D:\Projects\MyWebsite --on-modify "copy {path} D:\Backups\{name}_{timestamp}"
```

Automatically restart a web server when files change:
```bash
python file_monitor.py watch D:\Projects\MyWebsite --include "*.html" "*.php" --on-modify "systemctl restart apache2"
```

Monitor with lower latency (quicker response):
```bash
python file_monitor.py watch D:\Projects\MyWebsite --latency 0.5
```

Generate a detailed log file:
```bash
python file_monitor.py watch D:\Projects\MyWebsite --log-file website_changes.log
```

Track changes, preserving entire history in a database:
```bash
python file_monitor.py watch D:\Projects\MyWebsite --history-db changes.db
```

### Complete Command Line Parameters

```
usage: file_monitor.py [-h] {watch,status,stop} ...

File System Change Monitor - Monitor directories for file changes in real-time

positional arguments:
  {watch,status,stop}   Commands
    watch               Start monitoring a directory
    status              Show status of active monitors
    stop                Stop a running monitor

common options:
  -h, --help            Show help information and exit
```

#### Watch Command Options

```
usage: file_monitor.py watch [-h] [--events {create,modify,delete,move} [{create,modify,delete,move} ...]]
                           [--include [INCLUDE ...]] [--exclude [EXCLUDE ...]]
                           [--recursive] [--no-recursive]
                           [--on-create COMMAND] [--on-modify COMMAND]
                           [--on-delete COMMAND] [--on-move COMMAND]
                           [--copy-to DIRECTORY] [--latency SECONDS]
                           [--batch-events] [--ignore-editor-files]
                           [--log-file LOGFILE] [--history-db DATABASE]
                           [--daemon] [--pid-file PIDFILE]
                           [--buffer-size BUFFER_SIZE] [-q] [-v]
                           path

positional arguments:
  path                  Directory path to monitor

options:
  -h, --help            Show help information and exit
  --events {create,modify,delete,move} [{create,modify,delete,move} ...]
                        Event types to monitor (default: all)
  --include [INCLUDE ...]
                        File patterns to include (e.g., "*.py" "*.js")
  --exclude [EXCLUDE ...]
                        File patterns to exclude (e.g., "*.tmp" "~*")
  --recursive           Monitor subdirectories recursively (default)
  --no-recursive        Don't monitor subdirectories
  --on-create COMMAND   Command to execute when files are created
  --on-modify COMMAND   Command to execute when files are modified
  --on-delete COMMAND   Command to execute when files are deleted
  --on-move COMMAND     Command to execute when files are moved/renamed
  --copy-to DIRECTORY   Copy changed files to this directory
  --latency SECONDS     Latency in seconds for detecting changes (default: 1.0)
  --batch-events        Batch multiple events occurring together
  --ignore-editor-files Ignore temporary files created by common editors
  --log-file LOGFILE    Log events to this file
  --history-db DATABASE Database file to store change history
  --daemon              Run monitor as a daemon process
  --pid-file PIDFILE    PID file path when running as daemon
  --buffer-size BUFFER_SIZE
                        Event buffer size (default: 8192)
  -q, --quiet           Quiet mode, reduce output
  -v, --verbose         Verbose mode, show more information
```

### Command Placeholders

When specifying commands with `--on-create`, `--on-modify`, etc., you can use the following placeholders:

- `{path}`: Full path to the affected file
- `{name}`: Base name of the file
- `{dir}`: Directory containing the file
- `{ext}`: File extension
- `{timestamp}`: Current timestamp (format: YYYYMMDD_HHMMSS)
- `{event}`: Event type (create, modify, delete, move)
- `{src_path}`: Source path (only for move events)
- `{dest_path}`: Destination path (only for move events)

### Examples of Command Integration

1. **Automatic code deployment**:
   ```bash
   python file_monitor.py watch src/ --include "*.php" --on-modify "scp {path} user@server:/var/www/{name}"
   ```

2. **Automatic backup**:
   ```bash
   python file_monitor.py watch important_docs/ --on-modify "powershell.exe -Command 'Copy-Item \"{path}\" -Destination \"D:\\Backups\\{name}_{timestamp}{ext}\"'"
   ```

3. **Automatic testing**:
   ```bash
   python file_monitor.py watch src/ --include "*.py" "*.js" --on-modify "pytest tests/"
   ```

4. **Database update trigger**:
   ```bash
   python file_monitor.py watch data/ --include "*.csv" --on-modify "python update_database.py {path}"
   ```

## text_merger.py - Text File Merger

This script provides functionality for merging multiple text files into a single file, with various sorting and formatting options.

### Features

- **Multiple Merging Modes**:
  - Simple concatenation (append files one after another)
  - Line-by-line merging (interleave lines from different files)
  - Smart merging (remove duplicates, sort content)
- **Flexible Sorting Options**:
  - Sort by line content (alphabetical)
  - Sort by line length
  - Sort by numeric value
  - Custom sort patterns
- **Text Processing Features**:
  - Remove duplicate lines
  - Filter lines by pattern
  - Add line prefixes/suffixes
  - Add file headers/footers
  - Trim whitespace
- **Output Formatting**:
  - Custom line separators
  - Custom file separators
  - Line numbering options
  - Preserve or strip comments

### Basic Usage

Merge all text files in the current directory:
```bash
python text_merger.py *.txt -o merged.txt
```

Merge specific files:
```bash
python text_merger.py file1.txt file2.txt file3.txt -o combined.txt
```

Merge and sort content:
```bash
python text_merger.py *.log -o sorted_logs.txt --sort
```

### Advanced Usage Examples

Merge files with custom separator between files:
```bash
python text_merger.py *.txt -o merged.txt --file-separator "==========\n"
```

Merge files and remove duplicate lines:
```bash
python text_merger.py *.csv -o merged.csv --unique
```

Sort lines numerically:
```bash
python text_merger.py numbers*.txt -o sorted_numbers.txt --sort numeric
```

Add line numbers:
```bash
python text_merger.py code*.py -o all_code.py --line-numbers
```

Filter lines matching a pattern:
```bash
python text_merger.py *.log -o errors.log --include "ERROR:"
```

Exclude lines matching a pattern:
```bash
python text_merger.py *.log -o clean.log --exclude "DEBUG:"
```

Merge and add file names as headers:
```bash
python text_merger.py *.txt -o merged.txt --add-filename-header
```

### Complete Command Line Parameters

```
usage: text_merger.py [-h] [-o OUTPUT] [--sort {alpha,numeric,length,natural}]
                     [--reverse] [--unique] [--line-separator LINE_SEPARATOR]
                     [--file-separator FILE_SEPARATOR] [--include PATTERN]
                     [--exclude PATTERN] [--line-numbers] [--add-filename-header]
                     [--trim-whitespace] [--ignore-empty] [--ignore-comments]
                     [--comment-char COMMENT_CHAR] [--encoding ENCODING]
                     files [files ...]

Text File Merger - Combine multiple text files with various options

positional arguments:
  files                 Files to merge

options:
  -h, --help            Show help information and exit
  -o, --output OUTPUT   Output file (default: stdout)
  --sort {alpha,numeric,length,natural}
                        Sort lines (alpha: alphabetically, numeric: numerically,
                        length: by line length, natural: natural sort)
  --reverse             Reverse sort order
  --unique              Remove duplicate lines
  --line-separator LINE_SEPARATOR
                        Line separator for output (default: system newline)
  --file-separator FILE_SEPARATOR
                        Text to insert between merged files
  --include PATTERN     Only include lines matching pattern
  --exclude PATTERN     Exclude lines matching pattern
  --line-numbers        Add line numbers to output
  --add-filename-header Add source filename as header before file content
  --trim-whitespace     Trim whitespace from beginning and end of lines
  --ignore-empty        Ignore empty lines
  --ignore-comments     Ignore comment lines
  --comment-char COMMENT_CHAR
                        Character that marks comment lines (default: #)
  --encoding ENCODING   File encoding (default: utf-8)
```

## file_split.py - File Splitting Tool

This script allows splitting large files into smaller parts using various splitting methods.

### Features

- **Multiple Splitting Methods**:
  - Split by line count (fixed number of lines per file)
  - Split by file size (fixed size per file)
  - Split by content pattern (e.g., when a specific pattern is found)
  - Split by logical sections (e.g., XML elements, JSON objects)
- **Smart Splitting Options**:
  - Preserve headers in each split file
  - Keep logical units intact
  - Handle binary files
- **Output Naming**:
  - Custom naming patterns for split files
  - Sequential numbering
  - Date/time-based naming
  - Content-based naming
- **Preview and Analysis**:
  - Preview split points without actually splitting
  - Analyze file structure before splitting
  - Estimate resulting file sizes

### Basic Usage

Split a large file into parts with 1000 lines each:
```bash
python file_split.py large_file.csv --lines 1000
```

Split a file into parts of 10MB each:
```bash
python file_split.py large_file.dat --size 10M
```

Split a log file at each date change:
```bash
python file_split.py server.log --pattern "^\[\d{4}-\d{2}-\d{2}\]"
```

### Advanced Usage Examples

Split CSV file and keep header row in each part:
```bash
python file_split.py large_data.csv --lines 5000 --keep-header 1
```

Split with custom output naming pattern:
```bash
python file_split.py access.log --lines 10000 --output "access_part_{num}.log"
```

Split XML file at each root element:
```bash
python file_split.py data.xml --xml-split "//record"
```

Split JSON file at each array element:
```bash
python file_split.py data.json --json-split "$.items[*]"
```

Preview split without actually creating files:
```bash
python file_split.py large_file.txt --lines 1000 --dry-run
```

Split binary file by size with specific buffer size:
```bash
python file_split.py large_image.raw --size 50M --binary --buffer-size 1M
```

### Complete Command Line Parameters

```
usage: file_split.py [-h] [--lines LINES | --size SIZE | --pattern PATTERN |
                    --xml-split XPATH | --json-split JSONPATH]
                    [--output OUTPUT] [--keep-header LINES] [--binary]
                    [--buffer-size SIZE] [--encoding ENCODING] [--dry-run]
                    [--overwrite] [-q] [-v]
                    file

File Splitting Tool - Split large files into smaller parts

positional arguments:
  file                  File to split

split options:
  -h, --help            Show help information and exit
  --lines LINES         Split by number of lines
  --size SIZE           Split by file size (format: n[K|M|G])
  --pattern PATTERN     Split when line matches pattern (regular expression)
  --xml-split XPATH     Split XML file using XPath expression
  --json-split JSONPATH Split JSON file using JSONPath expression

output options:
  --output OUTPUT       Output filename pattern (use {num} for sequence number)
  --keep-header LINES   Number of header lines to repeat in each split file
  --binary              Process file in binary mode
  --buffer-size SIZE    Buffer size for reading (format: n[K|M])
  --encoding ENCODING   File encoding (default: utf-8)
  --dry-run             Preview split without creating files
  --overwrite           Overwrite existing files
  -q, --quiet           Quiet mode, reduce output
  -v, --verbose         Verbose mode, show more information
```

## text_replace.py - Text Search and Replace Tool

This script provides functionality for searching and replacing text across multiple files, supporting regular expressions and various filtering options.

### Features

- **Powerful Search Capabilities**:
  - Plain text search
  - Regular expression search with capture groups
  - Case-sensitive or case-insensitive search
  - Whole word matching
- **Flexible Replacement Options**:
  - Simple text replacement
  - Regular expression replacement with backreferences
  - Function-based replacement (using Python expressions)
  - Conditional replacement
- **File Selection and Filtering**:
  - Process multiple files with glob patterns
  - Recursive directory processing
  - Filter by file extension
  - Include/exclude files by pattern
- **Safety Features**:
  - Preview changes before applying
  - Create backups of modified files
  - Detailed replacement reports
  - Undo previous replacements

### Basic Usage

Simple text replacement in a single file:
```bash
python text_replace.py -s "old text" -r "new text" file.txt
```

Replace using regular expressions:
```bash
python text_replace.py -s "user(\d+)" -r "account\1" --regex *.txt
```

Replace in all text files recursively:
```bash
python text_replace.py -s "Company A" -r "Company B" --recursive *.txt
```

### Advanced Usage Examples

Case-insensitive search:
```bash
python text_replace.py -s "warning" -r "CAUTION" --ignore-case logs/*.log
```

Preview changes without modifying files:
```bash
python text_replace.py -s "TODO" -r "FIXME" --dry-run *.py
```

Create backups before replacing:
```bash
python text_replace.py -s "old API" -r "new API" --backup *.js
```

Replace only whole words:
```bash
python text_replace.py -s "log" -r "logger" --whole-word *.py
```

Replace with regular expression groups:
```bash
python text_replace.py -s "(\d{2})-(\d{2})-(\d{4})" -r "\3-\1-\2" --regex *.csv
```

Count occurrences without replacing:
```bash
python text_replace.py -s "error" --count-only logs/*.log
```

Generate detailed report of changes:
```bash
python text_replace.py -s "deprecated" -r "obsolete" --report changes.txt *.java
```

### Complete Command Line Parameters

```
usage: text_replace.py [-h] -s SEARCH [-r REPLACE] [--regex] [--ignore-case]
                      [--whole-word] [--backup] [--dry-run] [--recursive]
                      [--include PATTERN] [--exclude PATTERN]
                      [--max-depth DEPTH] [--encoding ENCODING]
                      [--count-only] [--report FILE] [--undo UNDO]
                      [--max-replace MAX] [-q] [-v]
                      files [files ...]

Text Search and Replace Tool - Find and replace text across multiple files

positional arguments:
  files                 Files to process (supports glob patterns)

required options:
  -s, --search SEARCH   Text to search for

replacement options:
  -r, --replace REPLACE Text to replace with
  --regex               Use regular expressions for search and replace
  --ignore-case         Ignore case when searching
  --whole-word          Match whole words only
  --backup              Create backup of modified files (.bak extension)
  --dry-run             Preview changes without modifying files
  --recursive           Process directories recursively
  --include PATTERN     Only include files matching pattern
  --exclude PATTERN     Exclude files matching pattern
  --max-depth DEPTH     Maximum recursion depth
  --encoding ENCODING   File encoding (default: utf-8)
  --count-only          Only count occurrences, don't replace
  --report FILE         Generate detailed report of changes
  --undo UNDO           Undo replacements from specified report file
  --max-replace MAX     Maximum replacements per file (0 for unlimited)
  -q, --quiet           Quiet mode, reduce output
  -v, --verbose         Verbose mode, show more information
```

## image_processor.py - Image Batch Processing Tool

This script provides functionality for batch processing images, including resizing, format conversion, watermarking, and applying various filters and effects.

### Features

- **Image Transformation**:
  - Resize images (by percentage, dimensions, or to fit within bounds)
  - Crop images (by coordinates or automatic content-aware cropping)
  - Rotate and flip images
  - Convert between different image formats (JPG, PNG, GIF, WEBP, etc.)
- **Image Enhancement**:
  - Adjust brightness, contrast, saturation
  - Apply sharpening or blurring
  - Auto-enhance images
  - Apply various filters (grayscale, sepia, etc.)
- **Watermarking and Annotations**:
  - Add text watermarks with customizable font, size, color, and position
  - Add image watermarks with opacity control
  - Add borders and frames
  - Batch rename with customizable patterns
- **Metadata Management**:
  - Preserve, modify, or strip EXIF data
  - Add or update image metadata
  - Generate metadata reports

### Basic Usage

Resize all images in a directory:
```bash
python image_processor.py -i "photos/*.jpg" --resize 50%
```

Convert images to a different format:
```bash
python image_processor.py -i "images/*.png" --convert jpg
```

Add a watermark to images:
```bash
python image_processor.py -i "photos/*.jpg" --text-watermark "© 2023" --position bottom-right
```

### Advanced Usage Examples

Resize images to specific dimensions:
```bash
python image_processor.py -i "photos/*.jpg" --resize 800x600
```

Resize images while maintaining aspect ratio:
```bash
python image_processor.py -i "photos/*.jpg" --resize "max:1024x768"
```

Crop images:
```bash
python image_processor.py -i "photos/*.jpg" --crop 100,100,500,500
```

Apply multiple effects:
```bash
python image_processor.py -i "photos/*.jpg" --brightness 1.2 --contrast 1.1 --sharpen
```

Convert format and optimize for web:
```bash
python image_processor.py -i "images/*.png" --convert webp --quality 80 --optimize
```

Add image watermark:
```bash
python image_processor.py -i "photos/*.jpg" --image-watermark logo.png --opacity 0.3
```

Process images recursively:
```bash
python image_processor.py -i "photos/**/*.jpg" --resize 50% --recursive
```

Rename files based on EXIF data:
```bash
python image_processor.py -i "photos/*.jpg" --rename "{date}_{sequence}.jpg"
```

### Complete Command Line Parameters

```
usage: image_processor.py [-h] -i INPUT [--output-dir DIR] [--resize DIMENSIONS]
                         [--crop COORDINATES] [--rotate DEGREES] [--flip {h,v,both}]
                         [--convert FORMAT] [--quality QUALITY] [--optimize]
                         [--brightness FACTOR] [--contrast FACTOR]
                         [--saturation FACTOR] [--sharpen] [--blur RADIUS]
                         [--grayscale] [--sepia] [--auto-enhance]
                         [--text-watermark TEXT] [--font FONT] [--font-size SIZE]
                         [--font-color COLOR] [--position {top-left,top-center,top-right,
                                                         center-left,center,center-right,
                                                         bottom-left,bottom-center,bottom-right}]
                         [--image-watermark FILE] [--opacity OPACITY]
                         [--border WIDTH] [--border-color COLOR]
                         [--rename PATTERN] [--keep-exif] [--strip-exif]
                         [--recursive] [--threads NUM] [--dry-run] [-q] [-v]

Image Batch Processing Tool - Process multiple images with various operations

required options:
  -i, --input INPUT     Input files (supports glob patterns like "*.jpg")

output options:
  --output-dir DIR      Output directory (default: same as input with "_processed" suffix)
  --resize DIMENSIONS   Resize images (format: WIDTHxHEIGHT, PERCENTAGE%, or max:WIDTHxHEIGHT)
  --crop COORDINATES    Crop images (format: LEFT,TOP,RIGHT,BOTTOM or auto)
  --rotate DEGREES      Rotate images by specified degrees
  --flip {h,v,both}     Flip images (h: horizontal, v: vertical, both: both directions)
  --convert FORMAT      Convert images to specified format (jpg, png, webp, etc.)
  --quality QUALITY     Output quality for lossy formats (1-100)
  --optimize            Optimize images for smaller file size

enhancement options:
  --brightness FACTOR   Adjust brightness (1.0 is unchanged, >1 brighter, <1 darker)
  --contrast FACTOR     Adjust contrast (1.0 is unchanged, >1 more contrast, <1 less contrast)
  --saturation FACTOR   Adjust saturation (1.0 is unchanged, >1 more saturated, <1 less saturated)
  --sharpen             Sharpen images
  --blur RADIUS         Apply blur with specified radius
  --grayscale           Convert images to grayscale
  --sepia               Apply sepia tone effect
  --auto-enhance        Automatically enhance images

watermark options:
  --text-watermark TEXT Text to use as watermark
  --font FONT           Font for text watermark
  --font-size SIZE      Font size for text watermark
  --font-color COLOR    Font color for text watermark (name or hex code)
  --position {top-left,top-center,top-right,center-left,center,center-right,
             bottom-left,bottom-center,bottom-right}
                        Position for watermark
  --image-watermark FILE
                        Image file to use as watermark
  --opacity OPACITY     Opacity for image watermark (0.0-1.0)
  --border WIDTH        Add border with specified width
  --border-color COLOR  Border color (name or hex code)

file options:
  --rename PATTERN      Rename pattern (use {original}, {date}, {sequence}, etc.)
  --keep-exif           Preserve EXIF metadata
  --strip-exif          Remove all EXIF metadata
  --recursive           Process subdirectories recursively
  --threads NUM         Number of threads to use for processing
  --dry-run             Preview changes without modifying files
  -q, --quiet           Quiet mode, reduce output
  -v, --verbose         Verbose mode, show more information
```

## metadata_editor.py - File Metadata Editor

This script provides functionality for viewing, editing, and managing metadata in various file types, including images, audio, video, and documents.

### Features

- **Multi-format Support**:
  - Image files (JPEG, PNG, TIFF, etc.) - EXIF, IPTC, XMP metadata
  - Audio files (MP3, FLAC, WAV, etc.) - ID3 tags, Vorbis comments
  - Video files (MP4, MKV, AVI, etc.) - video and audio stream metadata
  - Document files (PDF, DOCX, etc.) - document properties
- **Comprehensive Metadata Processing**:
  - Read metadata from files
  - Add new metadata fields
  - Modify existing metadata
  - Delete specific metadata fields
  - Copy metadata between files
- **Batch Processing**:
  - Process multiple files at once
  - Recursive directory handling
  - Pattern matching for file selection
- **Import/Export Options**:
  - Export metadata to JSON, XML, or CSV
  - Import metadata from structured files
  - Generate metadata reports
  - Template-based metadata application
- **Safety Features**:
  - Backup files before modification
  - Dry-run mode to preview changes
  - Validation of metadata values

### Basic Usage

View metadata of a file:
```bash
python metadata_editor.py view photo.jpg
```

Set metadata field:
```bash
python metadata_editor.py set photo.jpg --field "Copyright" --value "© 2023 My Name"
```

Remove metadata field:
```bash
python metadata_editor.py remove photo.jpg --field "GPS*"
```

Export metadata to JSON:
```bash
python metadata_editor.py export photo.jpg --format json --output metadata.json
```

### Advanced Usage Examples

View specific metadata fields:
```bash
python metadata_editor.py view music.mp3 --fields "Title" "Artist" "Album"
```

Set multiple metadata fields:
```bash
python metadata_editor.py set document.pdf --field "Author" --value "John Doe" --field "Subject" --value "Report"
```

Batch set metadata for multiple files:
```bash
python metadata_editor.py set "photos/*.jpg" --field "Copyright" --value "© 2023 My Name" --recursive
```

Copy metadata from one file to another:
```bash
python metadata_editor.py copy --source template.jpg --target "photos/*.jpg"
```

Import metadata from JSON file:
```bash
python metadata_editor.py import photos.jpg --from metadata.json
```

Remove all GPS data from photos:
```bash
python metadata_editor.py remove "photos/*.jpg" --field "GPS*" --recursive
```

Generate a metadata report for all media files:
```bash
python metadata_editor.py report "media/**/*" --output report.csv --format csv --recursive
```

Preview changes without modifying files:
```bash
python metadata_editor.py set "photos/*.jpg" --field "Copyright" --value "© 2023" --dry-run
```

### Complete Command Line Parameters

```
usage: metadata_editor.py [-h] {view,set,remove,copy,export,import,report} ...

File Metadata Editor - View and edit metadata in various file types

commands:
  {view,set,remove,copy,export,import,report}
    view                View metadata of files
    set                 Set metadata fields
    remove              Remove metadata fields
    copy                Copy metadata between files
    export              Export metadata to file
    import              Import metadata from file
    report              Generate metadata report

common options:
  -h, --help            Show help information and exit
```

#### View Command

```
usage: metadata_editor.py view [-h] [--fields FIELD [FIELD ...]]
                              [--format {text,json,xml}] [--output FILE]
                              [--recursive] [-q] [-v]
                              files [files ...]

positional arguments:
  files                 Files to process (supports glob patterns)

options:
  --fields FIELD [FIELD ...]
                        Specific metadata fields to view (supports wildcards)
  --format {text,json,xml}
                        Output format (default: text)
  --output FILE         Output file (default: stdout)
  --recursive           Process directories recursively
  -q, --quiet           Quiet mode, reduce output
  -v, --verbose         Verbose mode, show more information
```

#### Set Command

```
usage: metadata_editor.py set [-h] [--field FIELD] [--value VALUE]
                             [--from-file FILE] [--backup] [--dry-run]
                             [--recursive] [-q] [-v]
                             files [files ...]

positional arguments:
  files                 Files to process (supports glob patterns)

options:
  --field FIELD         Metadata field to set (can be used multiple times)
  --value VALUE         Value for the field (can be used multiple times)
  --from-file FILE      Read field-value pairs from file
  --backup              Create backup before modifying
  --dry-run            Preview changes without modifying files
  --recursive           Process directories recursively
  -q, --quiet           Quiet mode, reduce output
  -v, --verbose         Verbose mode, show more information
```

## file_cleaner.py - File Cleaning Tool

This script helps find and delete temporary files, old files, or unnecessary files to free up disk space and keep your system organized.

### Features

- **File Identification**:
  - Find temporary files by common patterns and extensions
  - Identify old files based on access or modification time
  - Detect empty files and directories
  - Find duplicate files
  - Identify cache files from various applications
- **Flexible Filtering**:
  - Filter by file patterns (glob and regex)
  - Filter by file size (minimum and maximum)
  - Filter by file age (access, modification, creation time)
  - Include/exclude specific directories
- **Multiple Cleaning Modes**:
  - Report only mode (no deletion)
  - Interactive mode (prompt for each file)
  - Automatic mode (delete matching files)
  - Move to trash/recycle bin instead of permanent deletion
- **Safety Features**:
  - Dry run mode to preview what would be deleted
  - Protection for system files
  - Detailed logs of actions taken
  - Option to move files to a backup location instead of deleting

### Basic Usage

Find temporary files and report them:
```bash
python file_cleaner.py scan C:\Users\Username\Downloads --temp
```

Clean old files (not accessed in 90 days):
```bash
python file_cleaner.py clean C:\Users\Username\Documents --age 90
```

Find and delete empty files and directories:
```bash
python file_cleaner.py clean C:\Projects --empty
```

### Advanced Usage Examples

Find large files (>100MB) not accessed in 30 days:
```bash
python file_cleaner.py scan D:\ --age 30 --min-size 100M
```

Clean temporary files with interactive prompts:
```bash
python file_cleaner.py clean C:\Users\Username --temp --interactive
```

Find and clean cache files:
```bash
python file_cleaner.py clean C:\Users\Username\AppData --cache
```

Move old files to trash instead of deleting:
```bash
python file_cleaner.py clean C:\Users\Username\Downloads --age 60 --to-trash
```

Clean specific file types:
```bash
python file_cleaner.py clean C:\Users\Username\Downloads --include "*.tmp" "*.bak" "*.log"
```

Preview what would be cleaned without actually deleting:
```bash
python file_cleaner.py clean C:\Users\Username\Downloads --temp --dry-run
```

Clean duplicate files:
```bash
python file_cleaner.py clean C:\Users\Username\Pictures --duplicates
```

Generate a detailed report of cleaning:
```bash
python file_cleaner.py clean C:\Users\Username --temp --report cleanup_report.txt
```

### Complete Command Line Parameters

```
usage: file_cleaner.py [-h] {scan,clean} ...

File Cleaning Tool - Find and delete temporary or unnecessary files

commands:
  {scan,clean}
    scan                Scan for files without deleting
    clean               Find and delete matching files

common options:
  -h, --help            Show help information and exit
```

#### Scan Command

```
usage: file_cleaner.py scan [-h] [--temp] [--cache] [--backup] [--logs]
                           [--empty] [--duplicates] [--age DAYS]
                           [--access-age DAYS] [--create-age DAYS]
                           [--min-size SIZE] [--max-size SIZE]
                           [--include PATTERN [PATTERN ...]]
                           [--exclude PATTERN [PATTERN ...]]
                           [--exclude-dir DIR [DIR ...]]
                           [--report FILE] [--format {text,csv,json}]
                           [--recursive] [--follow-symlinks] [-q] [-v]
                           directories [directories ...]

positional arguments:
  directories           Directories to scan

options:
  --temp                Find temporary files
  --cache               Find cache files
  --backup              Find backup files
  --logs                Find log files
  --empty               Find empty files and directories
  --duplicates          Find duplicate files
  --age DAYS            Find files not modified in specified days
  --access-age DAYS     Find files not accessed in specified days
  --create-age DAYS     Find files created at least specified days ago
  --min-size SIZE       Minimum file size (format: n[K|M|G])
  --max-size SIZE       Maximum file size (format: n[K|M|G])
  --include PATTERN [PATTERN ...]
                        File patterns to include
  --exclude PATTERN [PATTERN ...]
                        File patterns to exclude
  --exclude-dir DIR [DIR ...]
                        Directories to exclude
  --report FILE         Save report to file
  --format {text,csv,json}
                        Report format (default: text)
  --recursive           Process directories recursively (default)
  --follow-symlinks     Follow symbolic links
  -q, --quiet           Quiet mode, reduce output
  -v, --verbose         Verbose mode, show more information
```

#### Clean Command

```
usage: file_cleaner.py clean [-h] [--temp] [--cache] [--backup] [--logs]
                            [--empty] [--duplicates] [--age DAYS]
                            [--access-age DAYS] [--create-age DAYS]
                            [--min-size SIZE] [--max-size SIZE]
                            [--include PATTERN [PATTERN ...]]
                            [--exclude PATTERN [PATTERN ...]]
                            [--exclude-dir DIR [DIR ...]]
                            [--interactive] [--dry-run] [--to-trash]
                            [--backup-dir DIR] [--report FILE]
                            [--format {text,csv,json}] [--recursive]
                            [--follow-symlinks] [-q] [-v]
                            directories [directories ...]

positional arguments:
  directories           Directories to clean

options:
  --temp                Clean temporary files
  --cache               Clean cache files
  --backup              Clean backup files
  --logs                Clean log files
  --empty               Clean empty files and directories
  --duplicates          Clean duplicate files (keeping one copy)
  --age DAYS            Clean files not modified in specified days
  --access-age DAYS     Clean files not accessed in specified days
  --create-age DAYS     Clean files created at least specified days ago
  --min-size SIZE       Minimum file size (format: n[K|M|G])
  --max-size SIZE       Maximum file size (format: n[K|M|G])
  --include PATTERN [PATTERN ...]
                        File patterns to include
  --exclude PATTERN [PATTERN ...]
                        File patterns to exclude
  --exclude-dir DIR [DIR ...]
                        Directories to exclude
  --interactive         Prompt before each deletion
  --dry-run             Preview what would be deleted without actually deleting
  --to-trash            Move files to trash/recycle bin instead of deleting
  --backup-dir DIR      Move files to backup directory instead of deleting
  --report FILE         Save cleaning report to file
  --format {text,csv,json}
                        Report format (default: text)
  --recursive           Process directories recursively (default)
  --follow-symlinks     Follow symbolic links
  -q, --quiet           Quiet mode, reduce output
  -v, --verbose         Verbose mode, show more information
```

### Safety Notes

- Always run with `--dry-run` first to see what would be deleted
- Use `--interactive` mode when unsure about files to be deleted
- Consider using `--to-trash` option for safer cleaning (files can be recovered)
- Be extremely careful when cleaning system directories
- Regular backups are recommended before major cleaning operations 