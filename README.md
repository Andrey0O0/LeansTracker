# LeansTracker
Простенькое мобильное приложение, созданное школьником на Python с использованием фреймворка [Flet](https://flet.dev/). Оно помогает отслеживать время ношения контактных линз, контролировать их срок службы и вовремя получать уведомления о необходимости замены.

## Сборка (APK)
#### Для Linux / macOS:
1. ```bash
   cd path/to/project
   ```
2. ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. ```bash
   pip install flet flet-android-notifications
   ```

#### Для Windows:
1. ```cmd
   cd path\to\project
   ```
2. ```cmd
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. ```cmd
   pip install flet flet-android-notifications
   ```

### 2. Сборка APK
```bash
flet build apk
```

### Важно: Решение проблем со сборкой Gradle

При сборке может возникнуть ошибка, связанная с `coreLibraryDesugaring` или `flutter_local_notifications`. 

Вам необходимо один раз внести следующие правки в сгенерированный файл `build/flutter/android/app/build.gradle.kts`:

1. В блоке `compileOptions` добавьте включение десугаризации:
   ```kotlin
   compileOptions {
       sourceCompatibility = JavaVersion.VERSION_17
       targetCompatibility = JavaVersion.VERSION_17
       isCoreLibraryDesugaringEnabled = true // ВАЖНО: Добавить эту строку
   }
   ```

2. Убедитесь, что в `kotlinOptions` используется строковое значение версии Java:
   ```kotlin
   kotlinOptions {
       jvmTarget = "17"
   }
   ```

3. В самом конце файла добавьте зависимость десугаризации в блок `dependencies`:
   ```kotlin
   dependencies {
       coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.1.4")
   }
   ```
```bash
flet build apk
```
