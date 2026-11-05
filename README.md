# Personal Site

A small static portfolio and notebook: a homepage with selected projects, a projects page, notes (posts), categories, an about page, and RSS. Plain HTML and one stylesheet, no build step.

## Edit

- **CV:** put your current CV at `cv.pdf` in the site root. Every page links to it.
- **Project photos:** images live in `images/`. Landscape photos around 16:10 crop best on cards. The quadruped card uses a render of its MuJoCo model (`images/hal-sim.jpg`); swap in a photo of the robot when there is one. The `.placeholder` style is still in the stylesheet if a project needs a "Photo needed" box.
- **Projects:** each project on `projects/index.html` has a title block (Role, When, Status, Tools), a "What I did" list and related links. The homepage cards link to these by anchor: the four large cards (`#haptic-wrist`, `#mobile-manipulator`, `#hopper`, `#quadruped`) and the six "More projects" cards (`#lightsaber`, `#test-suite`, `#teleoperation`, `#replicator`, `#sisyphus`, `#spherical-go`).
- **Publications:** listed on the homepage (`#publications`) and on `about/index.html`. Update both.
- **Posts:** copy one of the folders in `posts/`, then update `posts/index.html`, `categories/index.html` and `index.xml`. Add it to the homepage's "From the notebook" list if it belongs there.
- **Contact details** live in the header, the homepage hero, `about/index.html` and every page footer.
- Replace `https://example.com/` in `index.xml` with your live site URL.

## Preview

Open `index.html` in a browser. The links are relative, so no build step or local server is required.
