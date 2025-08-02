# Email Configuration Guide for Quality Clamps

## Overview
The Quality Clamps Flask application now includes automatic email notifications for:
- **New Orders**: Sent to sales@qualclamps.com when customers place orders
- **Contact Form Submissions**: Sent to sales@qualclamps.com when customers use the contact form

All emails are sent from: `postman@qualclamps.com`

## Configuration Required

### 1. Email Password Setup
You need to set the email password for `postman@qualclamps.com` in your `.env` file:

```bash
# Update this line in your .env file:
MAIL_PASSWORD='your_actual_email_password_here'
```

### 2. Email Server Settings
The current configuration assumes Gmail SMTP. If you're using a different email provider, update these settings in `.env`:

```bash
MAIL_SERVER='smtp.gmail.com'  # Change if not using Gmail
MAIL_PORT=587                 # Standard TLS port
```

### 3. For Gmail Users
If using Gmail, you may need to:
1. Enable "Less secure app access" OR
2. Use an "App Password" instead of your regular password
3. Enable 2-factor authentication and generate an app-specific password

## Email Templates

### Order Notification Email Includes:
- Order ID and customer information
- Complete order details (products, quantities, prices)
- Shipping information and costs
- Payment method and status
- Customer notes

### Contact Form Email Includes:
- Customer contact information
- Inquiry type
- Customer message
- Submission timestamp

## Testing
Run the test script to verify email functionality:

```bash
python3 test_email.py
```

## Email Flow

### For Orders:
1. Customer completes checkout
2. Order is saved to `data/orders.json`
3. Email notification is automatically sent to `sales@qualclamps.com`
4. Customer sees order confirmation page

### For Contact Forms:
1. Customer submits contact form
2. Email notification is immediately sent to `sales@qualclamps.com`
3. Customer sees success message

## Troubleshooting

### Common Issues:
1. **Authentication Failed**: Check email password and server settings
2. **No emails received**: Check spam folder, verify recipient email
3. **Connection timeout**: Verify SMTP server and port settings

### Debug Mode:
The app will print email status to console:
- "Order notification email sent for ORDER-ID"
- "Contact form notification email sent for CUSTOMER-NAME"
- Error messages if sending fails

## Security Notes
- Email password is stored securely in `.env` file
- `.env` file should be added to `.gitignore` to prevent password exposure
- Consider using app-specific passwords instead of main email passwords
