# Code injector
A web app for injecting code into different file types. Try a demo at injector.codes

The web app is an automated code injector that plants code into different file types to test for injection vulnerabilities that are as a result of file uploads. The app was initially made as one of the tools for the [Cysuite platform](https://cysuite.herokuapp.com)

### Features
- Automatically generate new file types e.g. PNG, JPEG and GIFs that are recognizable by the most common libraries and operating systems.
- Upload your own image/PDF for injection.
- Inject code (XSS, XXE, PHP shell code and SQL injections) in filename, contents or headers.
- Set custom image dimensions and file sizes to bypass website restrictions.