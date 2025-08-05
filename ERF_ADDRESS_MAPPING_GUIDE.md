# ERF Address Mapping System - Administrator Guide

## Overview

The ERF Address Mapping system provides centralized address management for Altona Village. It allows administrators to upload and manage ERF-to-address mappings, which enables automatic address auto-fill functionality throughout the application.

## Features

- **Bulk Upload**: Import ERF mappings from CSV or Excel files
- **Template Download**: Get a properly formatted template for data entry
- **Address Lookup**: Search and verify existing mappings
- **Auto-fill Integration**: Automatic address completion in registration and other forms
- **Data Management**: Edit, delete, and clear mapping data

## Getting Started

### 1. Access the Address Mappings Interface

1. Login as an administrator
2. Navigate to **Admin Dashboard**
3. Click **Address Mappings** in the left sidebar
4. You'll see the Address Mappings management interface

### 2. Download the Template

Before uploading data, download the template to ensure proper formatting:

1. Click the **Download Template** button
2. Open the downloaded CSV file in Excel or Google Sheets
3. The template contains three columns:
   - `erf_number`: The ERF number (e.g., 27727, 27728)
   - `street_number`: The street number (e.g., 15, 22A)
   - `street_name`: The street name (e.g., Oak Avenue, Pine Street)

### 3. Prepare Your Data

Fill in the template with your ERF data:

```csv
erf_number,street_number,street_name
27727,15,Oak Avenue
27728,17,Oak Avenue
27729,19,Oak Avenue
27730,21,Oak Avenue
27731,23,Oak Avenue
27800,1,Pine Street
27801,3,Pine Street
27802,5,Pine Street
```

**Important Notes:**
- ERF numbers must be unique
- Street numbers can include letters (e.g., 22A, 15B)
- Street names should be consistent (use the same format throughout)
- Remove any empty rows before uploading

### 4. Upload Your Data

1. Click **Choose File** in the upload section
2. Select your completed CSV or Excel file
3. Click **Upload Mappings**
4. The system will:
   - Validate the file format
   - Check for duplicate ERF numbers
   - Display any errors or warnings
   - Show a success message when completed

### 5. Verify Your Upload

After uploading:
1. Use the **Search ERF** field to look up specific ERF numbers
2. The table will show all current mappings
3. Verify that your data was imported correctly

## Managing Existing Data

### Searching and Viewing

- **Search**: Use the search box to find specific ERF numbers
- **Sorting**: Click column headers to sort the data
- **Pagination**: Browse through large datasets using the navigation controls

### Updating Data

To update existing mappings:
1. Download the current data (export feature coming soon)
2. Edit the CSV file with your changes
3. Clear existing data if needed (see below)
4. Re-upload the updated file

### Deleting Individual Entries

1. Find the ERF mapping you want to delete
2. Click the **Delete** button in the Actions column
3. Confirm the deletion

### Clearing All Data

⚠️ **Warning**: This action cannot be undone!

1. Click the **Clear All Mappings** button
2. Confirm that you want to delete all data
3. All ERF mappings will be permanently removed

## Auto-fill Functionality

Once ERF mappings are uploaded, users will automatically benefit from address auto-fill in:

- **Registration Forms**: New users can enter their ERF number and get auto-completed addresses
- **Property Management**: Property updates with automatic address lookup
- **Vehicle Registration**: Address fields auto-filled for vehicle owners
- **Any Future Forms**: The system is designed to work with any form that includes ERF and address fields

### How Auto-fill Works

1. User enters an ERF number (minimum 3 digits)
2. System automatically looks up the corresponding address
3. Street number and street name fields are automatically populated
4. User can still manually edit the auto-filled values if needed

## Data Quality Best Practices

### ERF Numbers
- Use consistent formatting (no spaces, special characters)
- Ensure each ERF number is unique
- Use numeric values only (letters not supported)

### Street Numbers
- Can include letters (15A, 22B)
- Keep formatting consistent within the same street
- Avoid special characters except letters

### Street Names
- Use full street names (not abbreviations)
- Be consistent with formatting (e.g., always "Oak Avenue", not "Oak Ave")
- Include street type (Avenue, Street, Road, etc.)

## Troubleshooting

### Upload Issues

**File Format Error**
- Ensure your file is CSV or Excel format
- Check that column headers match exactly: `erf_number`, `street_number`, `street_name`

**Duplicate ERF Numbers**
- The system will reject files with duplicate ERF numbers
- Check your data for duplicates before uploading
- Consider using Excel's "Remove Duplicates" feature

**Empty or Invalid Data**
- Remove any empty rows from your file
- Ensure ERF numbers are numeric
- Check that required fields are not empty

### Auto-fill Not Working

**No Results Found**
- Verify the ERF number exists in your uploaded mappings
- Check that the ERF number is entered correctly
- Ensure there are no leading/trailing spaces

**Partial Results**
- Some mappings may have incomplete data
- Review your uploaded data for missing street numbers or names

## API Endpoints

For developers integrating with the system:

### Public Endpoints (No Authentication Required)
```
GET /api/public/lookup-address/{erf_number}
```
Returns address data for the specified ERF number.

### Admin Endpoints (Authentication Required)
```
GET /api/admin/address-mappings - Get all mappings
POST /api/admin/address-mappings/upload - Upload new mappings
GET /api/admin/address-mappings/template - Download template
DELETE /api/admin/address-mappings/{erf_number} - Delete specific mapping
DELETE /api/admin/address-mappings - Clear all mappings
```

## Support

If you encounter issues:

1. Check this guide for solutions
2. Verify your data format matches the template
3. Test with a small sample file first
4. Contact your system administrator for technical support

## Data Backup

**Recommendation**: Before clearing all data or making major changes:
1. Export your current data (feature coming soon)
2. Keep backup copies of your original CSV files
3. Test changes with a small dataset first

## Future Enhancements

Planned features:
- Data export functionality
- Bulk editing interface
- Address validation integration
- Geographic coordinate support
- Street address standardization

---

*Last updated: [Current Date]*
*Version: 1.0*
