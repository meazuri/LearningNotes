

# How certificates and provisioning profiles work together for iOS development and distribution.

## Development:
Each developer requires two files:

- A Development Certificate (.cer), which can be exported as a .p12 file.

- A Development Provisioning Profile, which includes the certificate, app ID, and testing devices.

## Distribution:
- Each developer requires two files for app release:

- A Distribution Certificate (.p12), generated from the Mac used to create the CSR. This certificate can be shared with the entire team.

- A Distribution Provisioning Profile, tied to the app and distribution certificate.

- Alternative for Development:
The team lead can generate a Development Certificate, export it as a .p12, and share it with the team to streamline setup.

- Certificate Renewal:
All certificates must be renewed periodically, typically every 1–3 years, to maintain app signing and distribution capabilities.

- Certificate (.cer or .p12) = Who you are (identity).
- Provisioning profile (.mobileprovision) = Where & what your app can run on (devices/entitlements).
- .p12 includes private key → needed for CI/CD signing.
- Development = testing, Distribution = App Store release.



### 1.   Three Key Pieces

#### CSR 
- A CSR stands for Certificate Signing Request. It’s basically a file you generate on your Mac when you want Apple to create a certificate for you.

- It contains your public key (part of a cryptographic key pair).
- Apple uses the CSR to generate a certificate that is tied to your private key (which never leaves your Mac)

- This ensures that only someone with the private key can sign apps using that certificate. 

- A CSR is a request to Apple to create a certificate for you, containing your public key, so that your certificate will be uniquely tied to your Mac’s private key.

- CSR file is required to create Developer Cert and Distribution Cert

#### Certificate

- Proves your identity as a developer or team.
- Can be development or distribution.
- Need CRS file to generate certificate
- Comes in two forms:

    - .cer → certificate only

    - .p12 → certificate + private key (needed for Jenkins/CI)

#### Provisioning Profile

- Tells Apple where your app can run and what it can do.
- Contains:

    - App ID (your app’s identity)

    - Entitlements (permissions like push notifications, iCloud, etc.)

    - Certificate(s) it is valid with

    - Devices (for development or Ad-Hoc distribution)

    - Once a profile is created, it locks in all these details.
    - Any change to the app’s identity, capabilities, or signing info →  you need to generate a new provisioning profile.
    - Old profiles don’t automatically update; they are fixed snapshots at creation. So if you add something like push notification capibilities,
      profile will become invalid. and you need to refresh / update it. 


### 2. How They Connect

- A provisioning profile always includes one or more certificates.
- When you build/sign an app: 
     - Your App Code + Certificate (identity) + Provisioning Profile (permissions & devices) → Signed IPA

### 4. Certificate Types and Profile Types

##### 1. Development Certificate in .cer format
- Purpose: Used to sign apps for development/testing on real devices.
- Contains: Certificate issued by Apple (does not include private key).
- Usage:

    - Imported into Keychain Access on the Mac that generated the CSR.
    - Used by Xcode to sign development builds.
- Notes:

    - Private key is generated on the Mac; without it, the .cer cannot sign apps on another machine.
    - Can have multiple development certificates per team.

- Required to generate development provisioning profiles.

##### 2. Development Certificate in .p12 format
- Purpose: Used to sign apps for development/testing on real devices.
- Contains:
    - The developer certificate issued by Apple
    - The private key (essential for signing)
    - Format: .p12 (Password-protected bundle of certificate + private key)
    - Usage:
        - Imported into Keychain Access on a Mac
        - Used by Xcode or Jenkins to sign apps for testing
    - Notes:
        - Tied to your Apple ID / Team
        - Required to generate development provisioning profiles

##### 3. Development Provisioning Profile (.mobileprovision)
- Purpose: Allows an app to run on registered devices for testing.
- Contains:
    - App ID
    - Development certificate(s) ,Can include multiple certificates (Dev A, Dev B, shared)
    - Entitlements
    - Includes registered devices for testing ,Device UDIDs (for testing) 


- Usage:
    - Used in code signing for development builds
    - Must match a development certificate
- Notes:
    - Expiration: ~1 year
    - Cannot be used to submit apps to App Store

##### 3. Distribution Certificate


##### 4. Distribution Provisioning Profile (.mobileprovision)
- Purpose: Allows an app to be signed for distribution (App Store or Ad-Hoc).
- Contains:
    - App ID
    - Distribution certificate(s) that can sign the app
    - Entitlements
    - Devices (for Ad-Hoc only)

- Usage:
    - Used in code signing during archive/export
    - Must match a distribution certificate
- Notes:
    - Required for App Store submission
    - Expiration: ~1 year


### 4. How to decode Provision Profile 
- Run this command to decode the provisioning profile:
        - ``` security cms -D -i /path/to/YourProfile.mobileprovision ```
- This outputs the profile as XML/plist.
- Look for these keys:
        
    
| Key                           | Meaning                                           |
| ----------------------------- | ------------------------------------------------- |
| `ExpirationDate`              | The date the profile expires                      |
| `Entitlements`                | Permissions like push notifications, iCloud, etc. |
| `DeveloperCertificates`       | Certificates the profile is valid for             |
| `ProvisionedDevices`          | Devices allowed (for development/Ad-Hoc)          |
| `ApplicationIdentifierPrefix` | App ID prefix                                     |





### 4. Development Environment Setup

#### Step 1: Generate a developer certificate for each developer

- Each developer generates a Certificate Signing Request (CSR) from Keychain Access on their Mac.

- On the Apple Developer Portal, create a Development Certificate for each developer using their CSR.

- Each certificate is tied to that developer’s private key (stored locally on their Mac).

- ✅ Key point: This certificate is per developer, not per app, so the same developer certificate can be used across multiple apps/projects.

#### Step 2: Download and install certificates

- Developers download their .cer file.

- Double-click to install in Keychain Access, pairing the certificate with the private key.

- Optionally, export as .p12 if needed for another Mac.

- 💡 Note: Only the developer’s private key + certificate pair matters for signing.

#### Step 3: Create a Development Provisioning Profile

- Go to Apple Developer Portal → Profiles → Development → Create New Profile.

- Select the App ID / bundle ID of your project — provisioning profiles are tied to an app.

- Add all developer certificates (so everyone can sign).

- Add all device UDIDs for testing.

- Download and install the profile in Xcode.

- ✅ Key distinction:

    - Development provisioning profile → tied to a specific app (bundle ID) and devices.

    - Developer certificate → tied to a developer, can be reused across multiple apps/projects.

#### Step 4: Configure Xcode

- Open the project → Signing & Capabilities.

- Select the Team.

- Choose Automatic signing or manually select the development provisioning profile.

- Each developer can now build/run the app on the registered devices.

#### ✅ Summary:

- Developer certificates are per person and reusable.

- Development provisioning profiles are per app and must include all developers + devices for testing.


### Distribution setup 

For a proper Distribution Setup in iOS, you essentially need three things,
CSR (Certificate Signing Request), Distribution Certificate (.cer) and 
Distribution Provisioning Profile (.mobileprovision)

#### 1. Create Distribution Certificate

- A team member generates a CSR on their Mac. Generated locally on a Mac using Keychain Access → Certificate Assistant.Contains the public key; private key is generated locally and never leaves your Mac.

- In Keychain Access → Certificate Assistant → Request a Certificate from a Certificate Authority:

Enter your Apple ID email + Common Name.

Choose "Saved to disk".

- A CSR file (usually CertificateSigningRequest.certSigningRequest).

- A private key is also generated automatically and stored in your Keychain (not in the CSR file).

- In Apple Developer Portal → Certificates → Production / Distribution → create certificate with Upload the CSR file that was generated on the Mac.

- Download .cer → install in Keychain Access and and pairs with your private key.

- This certificate has a private key (needed to sign apps).

- If other team members need this certificate, export it from Keychain as a .p12 file (certificate + private key) with a password.

- ✅ Only one certificate can be shared across the team  for distribution unlike development

- Other developers who need it to distribute App,  can export the certificate + private key as a .p12 and import into their Mac.

- Then, all developers can use the same certificate to sign builds for release.

#### 2. Create Distribution Provision Profile


- Just like development, provisioning profiles are tied to an app, not a developer.So we need to create provision profile for each app but we can use same distribution certificate

- Include the distribution certificate in the profile.

- Can include multiple devices for Ad-Hoc, or none for App Store.

- Download .mobileprovision and add it to Xcode.

#### Key points:

- Only one distribution certificate per platform is usually enough for a team.

- Developers share the same distribution certificate if needed for signing/release.

- Provisioning profiles, not certificates, are app-specific

- iOS provisioning profiles are snapshots of your app’s capabilities and certificates at the time they are created.

- #### If you add or change capabilities (like push notifications, App Groups, or iCloud), the existing profile does not automatically update.
  #### In that case, the profile becomes invalid for the new capabilities and you need to regenerate or refresh the profile in Apple Developer Portal.After regenerating, you need to download and install the updated profile in Xcode.

## Renewal

### 1. Renew Developer Certificate
- Step 1: Check expiry
    - Go to Apple Developer Portal → Certificates → Development.
    - Find your developer certificate and check the expiration date.

- Step 2: Generate a new CSR

    - On your Mac: Keychain Access → Certificate Assistant → Request a Certificate from a Certificate Authority.
    - Save the CSR file to disk.
    - This generates a new private key on your Mac (CSR contains public key, private key stays local).

- Step 3: Create a new certificate

    - In Apple Developer Portal → Certificates → Add (+) → iOS Development
    - Upload the CSR.
    - Apple generates a new certificate (.cer).
    - Download and double-click to install in Keychain Access.
    
- Step 4 (Optional): Export .p12 for sharing

    - If other team members need the new certificate:
    - Right-click the certificate in Keychain → Export → Personal Information Exchange (.p12)
    - Protect with a password → share securely.

### 2. Renew Development Provisioning Profile

- Step 1: Edit or create a new profile

    -  Go to Apple Developer Portal → Profiles → Development.

    - Find your existing development profile → click Edit.

    - Select the new developer certificate you just created.

    - Ensure all devices you want for testing are included.

- Step 2: Download & install

    - Download the updated .mobileprovision file.

    - Double-click to install in Xcode.

- Step 3: Update Xcode project

    - Open your project → Signing & Capabilities.

    - Make sure the new profile is selected (or let Xcode handle Automatic Signing).

    - Clean & rebuild to test.

### ✅ Key points / best practices

Developer certificates are per developer, so each dev may need to renew their own if it expires.

Provisioning profiles are per app, and must include the current active certificates.

Always renew before expiry to avoid build failures or testing interruptions.
