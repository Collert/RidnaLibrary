# RidnaLibrary

Ridna Library is a Flask-Python ibrary inventory management application made for Ridne Slovo, a Ukrainian community center in New Westminster, BC. 
This tool was also designed as Andrew Dzobko's final project for CS50x at Harvard University.

# Functions and routes

## Database

### Account management

Ridna Library uses personal Google accounts as a mean to sign in and get user's basic information. This was implemented with Google Sign-In. 
For more infornation on any data collection and Google's privacy policy, visit https://developers.google.com/terms
Said information is stored on the app's postgresql database and includes: 
- User's first and last name
- User's email adress
- User's Google profile picture
- User's Google id
- Unique school id, assigned after registration

### Inventory management

In addition to storing user information, app's database stores information about the books, namely:
- The title
- The name of the author
- The desctiption
- Book's unique id
- Information about book's inventory status, ie whether the book is borrowed, when it was borrowed and when is the expected return date
- Book's target audience

## Routes

### "/"

The home directory features a table of the books the user has already borrowed. This table includes the picture of a book, its name, the borrow and return dates

### "/profile"

This directory displays the profile of the current user, which includes all the relevant information about the user. 
Administrators are also able to access the subroute, that is student's school id, to view information about other users, including the books the currently hold.

### "/search"

This route allows users to look up any books offered by the library. It is possible lo look for a book using its id, or its Title or Author. As book titles recorded in Ukrainian, additional functionatity was provided for people who only have access to keyboards with latin caracters. 
The app will automatically translate all non-Ukrainian querries to Ukrainian as well as understand transliteration to provide accurate results.
The results are displayed in a form of Bootstrap cards, divided on pages with 15 books per page.

### "/borrow/(book id)"

This route executes appropriate database querries to mark the given book as borrowed, as well as fill in the start and the end of the borrowing period.
Teachers and library staff omit the 14-day limit and are given unlimited access to books.

### "/book/(book id)"

This route looks up the information about given book id and displays the information about it. This includes the rendering of the book, its name and description.
In addition, information about the author and books id is available at the bottom.
Below everything is a "Borrow" button that takes the user to /borrow route for the appropriate book.
Administrators can also see an additional tab that gives them access to editing and returning the book.

##### Administrator-only routes

All administrator routes are decorated with @admin_required function decorator that checks for user's role to prevent non-admins from accessing the routes below. If a non-admin user tries to access these routes, they will be redirected to their homepage.

### "/board"

This route allows library staff to view the books that were already borrowed by the library members. These books are grouped by their return dates on "Due today", "Due Soon" (Due in the next 3 days), "Overdue", and "Due later".
From this page, the librarian can also contact the borrower via email, as well as return the book.

### "/markout"

This route allows for the member of the staff to borrow the book under somebody else's name for the sake of convinience, or borrower inability to access the website.

### "/return/(book id)"

This route allows for the admin to return the book to the library. As this route doesn't render any templates, it opens up the ability to return books with a single link click, or as envisioned, by scanning the QR code on the back of the book.

### "/students"

This route allows admins to look up information about particular student by any information that's available about them.

## Misc

The website also features an interactive menu atop the screen to navigate it. This menu includes links to all mentioned routes as well as ways for users to contact the library directly, submit a bug report and toggle between light and dark theme.

The bug report feature allows users to submit any bug reports that will be automatically pulled into repo's issues tab via GitHub issues API.

Dark theme toggle is present for user's comfort in dark environments or asthetic preferences.