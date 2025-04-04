import 'package:flutter/material.dart';
import 'package:scholascan/homepage.dart';

class LoginPage extends StatelessWidget {
  final TextEditingController _usernameController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: const Color(0xFFF8F8F8), // AppBar color
        elevation: 0, // Remove AppBar shadow

        centerTitle: true,
        iconTheme: const IconThemeData(color: Colors.black), // Black back icon
      ),
      backgroundColor: const Color(0xFFF8F8F8), // Screen background color
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          const SizedBox(height: 50.0), // Space from the top
          const Center(
            child: Text(
              'ScholaScan',
              style: TextStyle(
                fontSize: 50.0,
                fontWeight: FontWeight.bold,
                color: Colors.black,
              ),
              textAlign: TextAlign.center,
            ),
          ),
          const SizedBox(height: 150),
          // Username and Password Fields
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0),
            child: Column(
              children: [
                TextField(
                  controller: _usernameController,
                  decoration: InputDecoration(
                    filled: true,
                    fillColor: Colors.white,
                    labelText: 'Username',
                    labelStyle: const TextStyle(color: Colors.black),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8.0),
                      borderSide: BorderSide.none,
                    ),
                  ),
                ),
                const SizedBox(height: 20.0),
                TextField(
                  controller: _passwordController,
                  obscureText: true,
                  decoration: InputDecoration(
                    filled: true,
                    fillColor: Colors.white,
                    labelText: 'Password',
                    labelStyle: const TextStyle(color: Colors.black),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8.0),
                      borderSide: BorderSide.none,
                    ),
                  ),
                ),
                const SizedBox(height: 30.0),
                // Submit Button
                ElevatedButton(
                  onPressed: () {
                    // Check if username and password are both "admin"
                    if (_usernameController.text == 'admin' &&
                        _passwordController.text == 'admin') {
                      // Navigate to HomePage
                      Navigator.pushReplacement(
                        context,
                        MaterialPageRoute(builder: (context) => HomePage()),
                      );
                    } else {
                      // Show error dialog for incorrect credentials
                      showDialog(
                        context: context,
                        builder: (context) => AlertDialog(
                          title: const Text('Login Failed'),
                          content: const Text(
                              'Incorrect username or password. Please try again.'),
                          actions: [
                            TextButton(
                              onPressed: () {
                                Navigator.of(context).pop(); // Close the dialog
                              },
                              child: const Text('OK'),
                            ),
                          ],
                        ),
                      );
                    }
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.black,
                    padding: const EdgeInsets.symmetric(
                        horizontal: 150.0, vertical: 25.0),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10.0),
                    ),
                  ),
                  child: const Text(
                    'Login',
                    style: TextStyle(color: Colors.white, fontSize: 16.0),
                  ),
                ),
              ],
            ),
          ),
          SizedBox(height: 20),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                _buildSocialIcon(
                  'https://img.lovepik.com/png/20231120/google-internet-icon-vector-Google-system-engineer_642910_wh860.png',
                ),
                _buildSocialIcon(
                  'https://thumbs.dreamstime.com/b/facebook-154683317.jpg',
                ),
              ],
            ),
          ),
          const SizedBox(height: 30.0), // Space at the bottom
        ],
      ),
    );
  }

  Widget _buildSocialIcon(String imageUrl) {
    return GestureDetector(
      onTap: () {
        // Handle social login action
      },
      child: CircleAvatar(
        radius: 30.0,
        backgroundColor: Colors.white,
        child: ClipRRect(
          borderRadius: BorderRadius.circular(30.0),
          child: Image.network(
            imageUrl,
            fit: BoxFit.cover,
            height: 40.0,
            width: 40.0,
          ),
        ),
      ),
    );
  }
}
