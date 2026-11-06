plugins {
    id("com.android.application")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

android {
    namespace = "com.yaufan.sharp_eyes"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    defaultConfig {
        // TODO: Specify your own unique Application ID (https://developer.android.com/studio/build/application-id.html).
        applicationId = "com.yaufan.sharpeyes"
        // You can update the following values to match your application needs.
        // For more information, see: https://flutter.dev/to/review-gradle-config.
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        // Uses the version code from pubspec.yaml. When using split APKs, 1000 * ABI_VERSION
        // is added automatically by Flutter. (https://developer.android.com/studio/build/configure-apk-splits#configure-APK-versions)
        // You can force using the value of versionCode by specifying the `-P force-version-code-ignoring-abi=true`
        // flag during build.
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    // The cloud builds sign with a test key that stays the same from build to
    // build (the repository's Actions secrets, as in the sibling apps), so a
    // new APK installs over the old one and what the child has played stays.
    // Without it (a build on your own computer) the debug key signs.
    val testKeystore = System.getenv("SHARP_EYES_KEYSTORE")?.let { file(it) }?.takeIf { it.exists() }
    signingConfigs {
        if (testKeystore != null) {
            create("test") {
                storeFile = testKeystore
                storeType = "pkcs12"
                storePassword = System.getenv("SHARP_EYES_KEYSTORE_PASSWORD")
                keyAlias = "kidspaint"
                keyPassword = System.getenv("SHARP_EYES_KEYSTORE_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            signingConfig = signingConfigs.getByName(if (testKeystore != null) "test" else "debug")
        }
    }
}

kotlin {
    compilerOptions {
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }
}

flutter {
    source = "../.."
}
