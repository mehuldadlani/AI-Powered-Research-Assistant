import 'package:flutter/material.dart';
import 'package:scholascan/loginpage.dart';
import 'package:scholascan/pages/chat_page.dart';

// Home Page with AppBar and updated Bottom Navigation
class HomePage extends StatefulWidget {
  @override
  _HomePageState createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int _selectedIndex = 0;

  final List<Widget> _pages = [
    HomeScreen(),
    SearchScreen(),
    BookScreen(),
    SettingsScreen(),
  ];

  void _onItemTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        toolbarHeight: 3,
        backgroundColor: const Color(0xFFF8F8F8),
        elevation: 0,
      ),
      body: _pages[_selectedIndex],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: _onItemTapped,
        selectedItemColor: Colors.black, // Selected item color
        unselectedItemColor: Colors.grey,
        backgroundColor:
            Colors.white, // Background color of BottomNavigationBar
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home, color: Colors.black), // Updated to black
            label: 'Home',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.search, color: Colors.black), // Updated to black
            label: 'Search',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.book, color: Colors.black), // Updated to black
            label: 'My Papers',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.settings, color: Colors.black), // Updated to black
            label: 'Settings',
          ),
        ],
      ),
    );
  }
}

// Dummy Research Papers Data
final List<Map<String, String>> researchPapers = [
  {
    "title": "The Future of AI in Healthcare",
    "author": "Dr. John Smith",
    "introduction":
        "This paper explores the applications of AI in modern healthcare...",
    "methodology":
        "Machine learning models were trained using real-world datasets...",
    "conclusion":
        "AI has the potential to revolutionize healthcare practices...",
  },
  {
    "title": "Quantum Computing Explained",
    "author": "Dr. Alice Johnson",
    "introduction": "Quantum computing is an emerging field...",
    "methodology": "By utilizing quantum bits (qubits), computations...",
    "conclusion": "Quantum computing promises exponential speedups...",
  },
  // Add more papers here
];

// Home Screen
class HomeScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            // Top tiles
            const Row(
              children: [
                SizedBox(width: 10),
                Expanded(
                  child: Card(
                    elevation: 5,
                    child: Padding(
                      padding: EdgeInsets.all(16.0),
                      child: Text(
                        "Recent Publications",
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            Expanded(
              child: ListView.builder(
                itemCount: researchPapers.length,
                itemBuilder: (context, index) {
                  final paper = researchPapers[index];
                  return Card(
                    elevation: 5,
                    child: ListTile(
                      title: Text(paper['title'] ?? ""),
                      subtitle: Text('Author: ${paper['author']}'),
                      onTap: () {
                        showDialog(
                          context: context,
                          builder: (context) {
                            return AlertDialog(
                              title: Text(paper['title'] ?? ""),
                              content: SingleChildScrollView(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      'Author: ${paper['author']}\n\nIntroduction:\n${paper['introduction']}\n\nMethodology:\n${paper['methodology']}\n\nConclusion:\n${paper['conclusion']}',
                                    ),
                                  ],
                                ),
                              ),
                              actions: [
                                TextButton(
                                  onPressed: () => Navigator.pop(context),
                                  child: const Text('Close'),
                                ),
                              ],
                            );
                          },
                        );
                      },
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// The other screens (Search, Book, and Settings) would follow a similar format.
// Search functionality filters based on the input.
// Elevated tiles and interactions are added for all pages.

// Search Screen
class SearchScreen extends StatefulWidget {
  @override
  _SearchScreenState createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final TextEditingController searchController = TextEditingController();
  final List<Map<String, String>> researchPapers = [
    {'title': 'AI and ML Advances', 'author': 'John Doe'},
    {'title': 'Quantum Computing Basics', 'author': 'Alice Smith'},
    {'title': 'Cybersecurity Trends', 'author': 'Jane Williams'},
    {'title': 'Blockchain in Finance', 'author': 'Michael Brown'},
  ];
  List<Map<String, String>> filteredPapers = [];

  @override
  void initState() {
    super.initState();
    filteredPapers = researchPapers;
  }

  void filterSearch(String query) {
    setState(() {
      if (query.isEmpty) {
        filteredPapers = researchPapers;
      } else {
        filteredPapers = researchPapers
            .where((paper) =>
                paper['title']!.toLowerCase().contains(query.toLowerCase()))
            .toList();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            TextField(
              controller: searchController,
              onChanged: filterSearch,
              decoration: InputDecoration(
                hintText: 'Search research papers...',
                prefixIcon: const Icon(Icons.search),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
            const SizedBox(height: 20),
            Expanded(
              child: ListView.builder(
                itemCount: filteredPapers.length,
                itemBuilder: (context, index) {
                  final paper = filteredPapers[index];
                  return Card(
                    elevation: 3,
                    child: ListTile(
                      title: Text(paper['title']!,
                          style: const TextStyle(fontWeight: FontWeight.bold)),
                      subtitle: Text('By ${paper['author']}'),
                      onTap: () {
                        // Show detailed research paper
                        showDialog(
                          context: context,
                          builder: (context) => AlertDialog(
                            title: Text(paper['title']!),
                            content: Text(
                                'Author: ${paper['author']}\n\nThis is the detailed description of the research paper.'),
                          ),
                        );
                      },
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// Book Screen
class BookScreen extends StatelessWidget {
  final List<Map<String, String>> myPapers = [
    {'title': 'AI Revolution', 'author': 'You'},
    {'title': 'Data Science Simplified', 'author': 'You'},
    {'title': 'The Future of Robotics', 'author': 'You'},
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Expanded(
              child: ListView.separated(
                itemCount: myPapers.length,
                separatorBuilder: (context, index) => const Divider(),
                itemBuilder: (context, index) {
                  final paper = myPapers[index];
                  return Card(
                    elevation: 3,
                    child: ListTile(
                      title: Text(paper['title']!,
                          style: const TextStyle(fontWeight: FontWeight.bold)),
                      subtitle: Text('By ${paper['author']}'),
                      onTap: () {
                        // Show detailed research paper
                        showDialog(
                          context: context,
                          builder: (context) => AlertDialog(
                            title: Text(paper['title']!),
                            content: Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Text(
                                    'Author: ${paper['author']}\n\nThis is the detailed description of your research paper.'),
                                const SizedBox(height: 20),
                                ElevatedButton(
                                  onPressed: () {
                                    // Generate and show summary
                                  },
                                  child: const Text('Generate Summary'),
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// Settings Screen
class SettingsScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          Card(
            elevation: 3,
            child: ListTile(
              title: const Text('Profile'),
              onTap: () {
                // Navigate to Profile Screen
                showDialog(
                  context: context,
                  builder: (context) => const AlertDialog(
                    title: Text('Profile'),
                    content: Text('Name: John Doe\nEmail: admin@example.com\n'),
                  ),
                );
              },
            ),
          ),
          Card(
            elevation: 3,
            child: ListTile(
              title: const Text('Join Us'),
              onTap: () {
                Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (context) => const ChatPage(),
                  ),
                );
              },
            ),
          ),
          Card(
            elevation: 3,
            child: ListTile(
              title: const Text('About Us'),
              onTap: () {
                // Show About Us content
                showDialog(
                  context: context,
                  builder: (context) => const AlertDialog(
                    title: Text('About Us'),
                    content: Text(
                        'ScholaScan: Bringing research closer to you.\n\nMakers: Pratham, Mehul, Nizammudin, Leon.'),
                  ),
                );
              },
            ),
          ),
          Card(
            elevation: 3,
            child: ListTile(
              title: const Text('Logout'),
              onTap: () {
                Navigator.pushReplacement(
                  context,
                  MaterialPageRoute(builder: (context) => LoginPage()),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
