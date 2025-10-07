 # IOS IPA Distribution to Jenkin CI-CD pipeline

## 1. The "Unsigned IPA" (A Misnomer)
This is the most confusing term because a truly unsigned IPA does not technically exist as a standard artifact. The process of creating an IPA in Xcode inherently involves signing.

- **What people really mean:** When someone asks for an "unsigned IPA," they usually mean the raw application bundle (.app) that exists deep inside Xcode's build folders before any signing or packaging has occurred. This is the YourApp.app file found in the DerivedData directory.
- **What it contains:** Just the compiled code, assets, storyboards, Info.plist, etc.
- **What it's missing:**
    - _CodeSignature folder (no signature).
    - embedded.mobileprovision file (no provisioning profile).
    - It's not a .ipa file at all; it's a .app folder structure.
- **When is it used?** Very rarely in modern CI. A re-signing tool could theoretically take this .app bundle, package it, and sign it from scratch, but it's an uncommon and brittle workflow. Most tools expect a fully formed IPA.
- **Your Jenkins Use Case:** This is almost certainly NOT what your Jenkins job needs.

## 2. The "Dev-Signed" IPA
This is a standard, well-defined artifact and a very common requirement for CI/CD pipelines.

- **What it is:** A complete .ipa file that has been properly signed using a Development Certificate and a Development Provisioning Profile.
- **How it's created:** By archiving your app in Xcode and exporting it using the "Development" distribution method.
- **What it contains:**
    - A valid _CodeSignature directory, signed with a development key.
    - An embedded.mobileprovision file that is a development profile.
- **When is it used?**
    - For deploying builds directly from Xcode to a developer's own registered test devices.
    - As an input for some re-signing systems. The structure is 100% correct, just signed with the "wrong" (non-distribution) identity.
- •Your Jenkins Use Case: This is a possible input for your Jenkins job. It's a valid IPA that can be re-signed.

## 3. The "Co-Signed" or "Ad Hoc Signed" IPA (The Most Common CI/CD Input)
This is the most precise and common term for the artifact needed by a re-signing service. It's often used interchangeably with "dev-signed," but it specifically refers to an IPA created for distribution outside the App Store.

- **What it is:** A complete .ipa file signed with either a Development Certificate or a Distribution (Ad Hoc) Certificate, but always bundled with an Ad Hoc Provisioning Profile. The term "co-signing" in this context refers to you (the developer) applying the initial signature before the CI server applies the final one.
- **How it's created:** By archiving your app in Xcode and exporting it using the "Ad Hoc" distribution method.
- **What it contains:**
    - A valid _CodeSignature directory.
    - An embedded.mobileprovision file that is an Ad Hoc profile, which includes a specific list of device UDIDs that are allowed to run the app.
    
- **•When is it used?**
    - For distributing test builds to a limited group of QA testers via a website or service like Firebase App Distribution.
    - This is the most common and ideal input for a Jenkins re-signing job. It's a fully-formed, distributable package that serves as a perfect template for the final App Store signing.

## How to Check the Files Inside an IPA
An .ipa file is just a standard ZIP archive with a different extension.
1. Don't Unzip, Just Rename: Find your .ipa file (e.g., MyApp.ipa).
2. Select the file and rename it, changing the extension from .ipa to .zip. (e.g., MyApp.zip).
3. Your Mac will ask for confirmation. Click "Use .zip".
4. Unarchive the ZIP: Double-click the newly renamed .zip file. This will create a folder named Payload.
5. Explore the App Bundle:
    - Inside the Payload folder, you will find your application bundle, which looks like a single file but is actually a folder (e.g., MyApp.app).
    - Right-click on the MyApp.app file and select "Show Package Contents".
You are now looking at all the raw files that make up your application, exactly as they will be installed on a device.

## What to Check: The 4 Most Important Things to Remember
When you're troubleshooting, you need to play detective. Here are the four most critical clues to look for inside your .app bundle.

### 1. The Provisioning Profile (embedded.mobileprovision)
This is the most important file for solving signing issues. It's the "rulebook" that was bundled with your app.
- **What to check:**
    - **Does it exist?** If it's missing, the app wasn't signed correctly.
    - **What's inside it?** You can inspect this file's contents with a command-line tool. Drag embedded.mobileprovision into a Terminal window and run this command (the full path will be pasted automatically):
    -  This command decodes and prints the contents of the profile
    ``security cms -D -i /path/to/your/embedded.mobileprovision``

- **Key things to note from the output:**
    - **Name:** Does this match the profile you intended to use (e.g., "My App Ad Hoc Profile")?
    - **AppIDName:** This shows the App ID (e.g., A1B2C3D4E5.* or A1B2C3D4E5.com.mycompany.myapp). Does it match your app's Bundle ID?
    - **Entitlements:** This is a critical section. Do the entitlements listed here (like get-task-allow or aps-environment) match what your app actually needs? This is a common source of crashes on launch.
    - **ProvisionedDevices:** If this is an Ad Hoc or Development profile, does this section exist? For App Store profiles, it will be absent.

### 2. The Code Signature (_CodeSignature/CodeResources)
This proves the app was actually signed and verifies its integrity.

- **What to check:**
    - **Does the _CodeSignature folder exist?** If not, the app is not signed.
    - You can run a command to verify the signature and see which certificate was used. Drag the .app bundle into a Terminal window to get its path:
    ``       codesign -dv --entitlements - /path/to/your/Payload/MyApp.app ``

### 3. The Match Between Profile and Signature (Entitlements)
This is the most critical and common point of failure.

- **What it is:** Your app has two separate places where its "special permissions" (called Entitlements) are listed:

    1. Inside the embedded.mobileprovision file: This is the "official record" of what permissions the App ID was granted by Apple when the profile was created.
    2. Baked into the Code Signature: This is the list of permissions that Xcode actually requested and embedded into the app's signature when you built it.
    
- **Why it's important:** These two lists must match perfectly. When a user launches your app, iOS acts like a security guard. It looks at both lists and asks: "Does the app's signed request for permissions match what the official provisioning profile says it's allowed to have?" If there is any difference, iOS will refuse to launch the app to protect the user's security.
- **How to check for a mismatch:** 
    1. Run the security command on the provisioning profile to see its entitlement list.
    2. Run the codesign command on the .app bundle to see the signature's entitlement list.
    3. Compare the two outputs side-by-side.•Analogy: You have a special license card (provisioning profile) that says you are allowed to drive a motorcycle. But when you get on the road, you tell the officer (the code signature) that you are trying to drive a truck. The officer sees that "truck" is not on your license card and immediately takes you off the road. Your app "crashes" on launch.
    
- **Common Mismatch Example:**
    - The embedded.mobileprovision lists aps-environment: development.
    - The codesign output lists aps-environment: production.
    - Result: Mismatch! The app will not launch or push notifications will fail

### 4. The Bundle ID (The App's Unique Name)
This seems simple, but a tiny mistake here breaks everything.

- **What it is:** The Bundle Identifier (e.g., com.mycompany.myapp) is your app's unique, universal name across the entire Apple ecosystem. It's how the App Store, iOS, and all services identify your specific app.
- **Why it's important:** The Bundle ID is the central key that links everything else together. The certificate is issued for a specific Team ID, the provisioning profile is issued for a specific App ID (which is tied to your Bundle ID), and your app's Info.plist must declare that same Bundle ID. If the name in your app's Info.plist doesn't match the name in the provisioning profile, the entire chain of trust is broken.
- **How to check for a mismatch:**
    1. Look at the CFBundleIdentifier value inside your app's Info.plist file.
    2. Look at the Identifier value from the output of the codesign command.
    3. Look at the AppIDName or application-identifier from the output of the security command on the provisioning profile.
- Analogy: Your name is "John Smith" on your birth certificate and passport. You get a driver's license (provisioning profile) issued to "John Smith." But when you fill out your car registration (Info.plist), you accidentally write your name as "Jon Smith." Even though it's a small typo, the system will reject your registration because the names do not match. The car cannot be legally driven.
- Conclusion:
    - Point 3 (Entitlements Match): Checks that the permissions requested by the app are the same as the permissions granted by the profile.
    - Point 4 (Bundle ID): Checks that the app's name is consistent across all documents (the app itself, the signature, and the profile).Getting these two things right will solve the vast majority of "it works on my machine but fails on Jenkins" or "the app crashes on launch" issues.
 
