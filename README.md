<h1>
  <img src="assets/logo.svg" alt="Logo" height="40" align="top">
  &nbsp;
  BookLink
</h1>

Connect your e-reader to any device—phone, tablet, or computer—wirelessly in seconds.
No cables, no apps, no complex setup required.

Visit [booklink.fnt.im](https://booklink.fnt.im) to get started.


## Features

 - **No cables**:
   Send e-books to your device without cables or special software
- **Compatibility**:
   Works with any browser-enabled e-reader and sending device
 - **One-time setup**:
   You need to pair your devices only once.
 - **Privacy**:
   Built with privacy by design. No user data is collected or needed.


## How it works

 1. Visit [booklink.fnt.im](https://booklink.fnt.im) on both your e-reader and second device
 2. Complete the quick pairing process (only needed once)
 3. Create bookmarks on both devices for one-click access in the future
 4. Start sending e-book files wirelessly to your e-reader


## Behind the scenes

The application core is built using plain Python and designed to operate without persistent storage.
Code is structured with a focus on modularity and testability, ensuring easy maintenance and extensibility.

Instead of requiring personal data for user registration, the system issues verifyable tokens for authentication.
This way, the service does not save any user data at all - not even anonymous data.
All file data is processed in-memory with a strict lifecycle, ensuring no data persists after processing.
This approach prioritizes user privacy and minimizes the risk of data exposure.

The system remains lightweight, requiring minimal resources and maintenance.
A thin Flask server provides the application backend through a REST API.
The frontend uses vanilla JavaScript, Tailwind CSS, and Daisy UI for a clean, responsive design with minimal dependencies.

For e-readers, a simplified interface ensures compatibility with devices that have limited browser capabilities.


## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
