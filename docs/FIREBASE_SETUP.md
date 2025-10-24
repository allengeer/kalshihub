# Firebase Setup Guide

This guide walks you through setting up Firebase for the market data persistence feature.

## 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project" or "Add project"
3. Enter a project name (e.g., "kalshihub-markets")
4. Choose whether to enable Google Analytics (optional)
5. Click "Create project"

## 2. Enable Firestore Database

1. In your Firebase project, go to "Firestore Database" in the left sidebar
2. Click "Create database"
3. Choose "Start in test mode" (we'll secure it later)
4. Select a location for your database (choose one close to your users)
5. Click "Done"

## 3. Create Service Account

You need service account credentials for the application to access Firebase:

1. Go to Project Settings (gear icon) → "Service accounts"
2. Click "Generate new private key"
3. Download the JSON file (e.g., `kalshihub-firebase-key.json`)
4. **Keep this file secure** - it contains sensitive credentials

## 4. Set Up Environment Variables

Create a `.env` file in your project root with the following content:

```bash
# Firebase Configuration
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_CREDENTIALS_PATH=path/to/your/service-account-key.json
FIREBASE_DATABASE_URL=https://your-project-id-default-rtdb.firebaseio.com/

# Market Crawler Configuration
CRAWLER_INTERVAL_MINUTES=30
CRAWLER_BATCH_SIZE=500
CRAWLER_MAX_RETRIES=3
CRAWLER_RETRY_DELAY_SECONDS=1

# Kalshi API Configuration
KALSHI_BASE_URL=https://api.elections.kalshi.com/trade-api/v2
KALSHI_RATE_LIMIT=20.0
```

Replace the placeholder values:
- `your-firebase-project-id`: Your actual Firebase project ID
- `path/to/your/service-account-key.json`: Path to your downloaded service account key

## 5. Deploy Schema

Once you have your environment set up, deploy the Firebase schema:

```bash
python scripts/deploy_schema.py
```

This will:
- Create the markets collection in Firestore
- Set up the schema metadata
- Validate the deployment

## 6. Test the Integration

Run the example script to test everything works:

```bash
python examples/firebase_example.py
```

This will:
- Deploy the schema (if not already deployed)
- Fetch markets from Kalshi API
- Store them in Firebase
- Demonstrate the crawler functionality

## 7. Security Rules (Optional)

For production, you should set up Firestore security rules. Go to Firestore Database → Rules and add:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Allow read/write access to markets collection
    match /markets/{document} {
      allow read, write: if true; // Adjust based on your security needs
    }

    // Allow read access to schema metadata
    match /_schema/{document} {
      allow read: if true;
      allow write: if false; // Only allow programmatic writes
    }
  }
}
```

## 8. Monitoring

You can monitor your Firebase usage in the Firebase Console:
- Firestore Database → Usage tab
- Project Settings → Usage tab

## Troubleshooting

### Common Issues:

1. **Authentication Error**: Make sure your service account key path is correct
2. **Permission Denied**: Check that your service account has the right permissions
3. **Project Not Found**: Verify your FIREBASE_PROJECT_ID is correct
4. **Schema Deployment Fails**: Check that Firestore is enabled and accessible

### Getting Help:

- Check the Firebase Console for error messages
- Review the application logs for detailed error information
- Ensure all environment variables are set correctly
