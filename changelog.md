Jasy 1.5-beta2
==============

## Major changes

### Introduction of new profile object

The new object is created by `State` like the `Session` instance and is mainly used to hold all relevant build information e.g. destination paths, formatting of output, compression settings, etc. This profile will be used for having a serialized version for validating cache entries against (still TODO).

The `Profile` also contains a typical application build tool under its `build()` method. This is mainly thought for omitting repeative tasks inside comparable applications where mostly 90% of the build script were identical. Applications are still being able to use some variant of the old API but it's typically preferred to switch over to the new, much simpler API.

The `Profile` also exports all destination paths to the client and making them available via `jasy.Env` e.g. `jasy.folder.js` etc.

### Integrated completely rewritten AssetManager (which replaces the old one)

- Removed support for profiles in asset system which is a major simplification and was only required by some edge cases at Zynga.
- New asset manager uses data from `Profile` for figuring out destination paths etc.
- Added support for auto tracking and registering of requested assets so that these are copied automatically to the destination just by requiring any details from them.
- Making asset methods available via new system command infrastructure to ask for asset details e.g. the build URL, image dimension, sprite data, etc. from within CSS or HTML templates.
- Improved and simplified implemention to support sprite sheets and image animations.

### Added new command interface

The command interface is a new API on the `Session` object to make shared commands available all different areas of the tooling. This is currently used by the new `AssetManager` to register commands for quering image URLs, dimensions, etc. The new API is planned for being used in the processors for Stylesheets, Templates, HTML files, etc. Like for `jasylibrary.py` to offer new APIs to the tooling of other projects, authors might now also create a `jasycommand.py` for making own commands available to other projects. Like for `jasylibrary.py` these commands are prefixed by the unique `name` of the project defining them.

### Continued work on style processor

- Major work on "execution" of style sheet code to process variables and system calls.
- New shared operation processor which is used by both, the Permutation and Execution engine to resolve comparisons, not-operators, etc.
- This version supports conditionals of variables (not just environment variables).
- Added new method `getMergedMTime()` for quering for the `@include` respecting modification time (figuring out the last changed file and returns that time instead of just the top-level file).
- Worked on include mechanics to improve stability of include implementation.
- The syntax of expressions have been modified. These now have to be wrapped inside `@expr()` for evaluation when not part of an assignment or conditional.
- Added a lot of new tests for validating the functionality of the new features. Updated old tests to new APIs, too.

### Minor changes through style processor work

- Temporary disabled style result caches to omit issues with too agressive caching (needs to be fixed with a later release).
- Added command wrapper `executeCommand` to `Util` for making command execution and result processing reuseable inside the style processor.
- Added new `castNativeToNode()` to `Util` for translating Python values into matching `Node` instances. This new class is used during variable processing (execution) for replacing operations with result nodes.
- Cleanup of style compressor from unnecessary prefixes and operators.
- Added support for slashes inside property values e.g. `font-size: 10px/1.2;`.
- Added support for raw values via `@raw("some css string");`. This is mainly used for supporting non-CSS values like old IE filter values (opacity, gradient, etc.).
- Added support for CSS `font-face`.
- Added new `noscope` flag to `Node` for marking specific blocks as not being scope relevant. This is currently used for if/else blocks to allow the content blocks to modify the parent block instead of scoping into the own block. This allows for defining/overriding variables inside if/else blocks.
- Minor fixes for CSS selector support not correctly supporting specific selector variants e.g. `&[attribute]`.
- Added support for reducing unneeded blocks (which are not allowed in CSS anyway but might be used for scoping variables) so that their content is injected in place of the original block.
- Removed some unsupport syntax constructs will processed inside the `Tokenizer` but not available in the `Parser`.

### Cleanup of sprite sheet generator

- Removed rotation feature (not relevant for most use cases and never was finished regarding implementation) and cleaned up a ton of code inside the whole sprite generator implementation.
- Simplified import logic for Python image module. Completely switched to Pillow which is much better than good old PIL nowadays.




## Minor changes

- Added support for return values from tasks (returning error codes from tasks ends Jasy with exactly the same error code now - thanks to Sebastian Fastner)
- Reworked integration of documentation generator to correctly work with [ReadTheDocs](http://jasy.readthedocs.org/en/latest/)
- Let `ImageInfo` class make use of shared implementation of file SHA1 hashing in `File` instead of using a local implementation.
- Removal of preliminary module for file system daemon support.
- Updated dependencies to new versions.
- Minor fixes for supporting YAML configuration files.
- Added new asset type info for `.md` and `.yaml` (both as "text").
- Moved `jasy.js.parse.ScopeData` to `jasy.parse.ScopeData` and updated references accordingly.




Jasy 1.5-beta1
==============

## Stylesheets

### Short Feature Overview

There is a fullblown CSS parser/compressor with custom features you know from LESS, Sass and Stylus. There are still a few (small and big) outstanding features but this is a good start:

- Added full blown CSS-like parser with added features like includes, dependencies, mixins, extends and variables.
- Added AST reducer to reduce custom style format into something CSS compatible.
- Added compressor for AST to generated CSS out of the reduced tree. Supports both compressed output and some basic formatting with line breaks.
- Styles are being loaded from the source folder `styles` and should be typically written out to `css` (by convention).
- Important: These stylesheets are not be part of the asset handling anymore. You have to generate the CSS files in both `source` and `build` targets. There might also be changes required for loading other assets like images from within such a stylesheet. Asset handling for stylesheets is not yet included.

### Changes to other APIs

To support the new stylesheet feature changes to other APIs were required:

- Revamped script APIs to be more explicitely oriented on scripts to make room for adding matching APIs for stylesheet processing e.g. `storeKernelScript()` instead of `storeKernel()`, `storeLoaderScript()` instead of `storeLoader()`, etc.
- Added abstract Classes `Resolver`, `Sorter` and `Node` to being used by both the stylesheet and script infrastructure. Therefor changed a few APIs to match generic usability of methods e.g. `add()` instead of `addClass()`, `getSorted()` instead of `getSortedClasses()`, etc.
- Added new API to output manager `storeCompressedStylesheet(styles)` for compressing a sorted set of stylesheets.
- Changed conventions to unify stylesheets and scripts: Put all your generated JavaScript files into `js` instead of `script` to match the file extension. This typically requires minor changes to the way these files are loaded into the HTML e.g. via `ScriptLoader`.
- Added abstract `FlagSet` class which is used for storing the flags for optimization and formatting settings in a unified way.
- Removed `name` support in `MetaData` as this is mainly not used anymore through the introduction of `content` sections inside `jasyproject` files.


## Other Changes/Optimizations:

- Let travis.ci use Python-3.3 instead of Python-3.2
- Reworked API documentation to be compatible with readthedocs.org. Published to http://jasy.readthedocs.org/en/latest/
- Improved session cleanup logic so if you ever wondered about caching issues for generated virtual files or locales these should be gone now. Cleaning now removes generated/virtual classes as well. No worry: These will be automatically re-generated when needed.
- Added new `jasy.version` field into each build to have client side access to the version of Jasy used during the build.
- Added `executeCommand` to the `jasyscript.py` environment automatically.
- Added support for "not" type handling in `DeadCode` elimination for JavaScript.
- Added asset handling support for JPEG-XR and WEBP image formats

## Fixes/Cleanups:

- Fixed HTTP server support for WOFF fonts to send the correct mime type
- Some internal optimizations for importing own modules making code cleaner and more robust
- Removed pretty useless "context" info when generating/processing AST trees and simplified code in `ClassItem`.
- Prefixed all cache items in `ClassItem` and `StyleItem` with either "script" or "style" to prevent conflicts between same IDs between these types.
- Removed "size" info (about compressed/permutated file size) from `ClassItem` and API data
- Cleanup of hoisting code in JavaScript parser. This was some old code from Narcissus and was never actually used because of the `ScopeAnalyzer` in Jasy which does somewhat the same and is also used during tree updates during the different optimization steps.
- Cleanup of `save()` and `rewind()` of the JavaScript `Tokenizer` which were never actually used.



Jasy 1.1.1
==========

- Minor bugfixes in HTTP handling
- Minor bugfixes in JavaScript optimizer for declarations



Jasy 1.1.0
==========

## New:

- Completely revamped integration of asset data. This data is now part of each individual build file and lays the ground for splitted builds (e.g. generate more than one output script for large applications) without adding all asset data to the kernel script.
- Completely revamped integration of permutations and their dependending detection classes. The new system is unbelievable smart. Fields can now depend on other fields and could use them in their detection logic as well. Jasy is capable of integration all the field info and detection automatically.
- Integrated Base62 API based on Sebastian Fastners JavaScript implementation
- Added support for hashed asset names (SHA1/Base62 of content based)
- Changed placeholder fields in jasyscript.py from `$name` to `{{name}}` which makes them safer to parse and easier to see
- Added basic Subversion support (figuring out current revision/branch)
- Added support for time/revision based output names e.g. for all generated JavaScript files. Changes to the revision (new commit) automatically produces different output files now.
- Added support for so-called virtual projects (projects which are generated on-the-fly to contain specific generated classes (e.g. field configuration, asset data, translation data, ...). This allows for using the standard cache procedures in Jasy and makes things in OutputManager way cleaner than before.
- Integrate environment ID generation which contains the hostname, host ID and username. This info will be passed through the kernel.js to the running application. This way it's easy to figure out where and from whom the current application was built.

## Changes/Fixes:

- Fixed task runtime calculation for tasks where the duration is longer than 10 seconds.
- Improved wrapper around PIL/Pillow integration (image sprite support)
- Improves cache handling
- Updated versions of dependencies to newer versions
- Using LooseVersion for every version check in Doctor
- Cleanup of old error handling in API system. This was pretty much broken recently and will be implemented better later on.
- Minor bugfixes (compiler, optimizer, build logic, ...)
- Updated some links from zynga to sebastian-software


Jasy 1.0.2
==========

- Path in session object into libraries so that these can execute information about other projects etc.
- Limit HTTP mirroring feature with additional flag for only mirror responses with status code of 200.
- Enforce "requests" version 0.14.1 in requirements.txt as 0.14.2 is buggy in Python 3. Waiting for 0.14.3 (See also: https://github.com/kennethreitz/requests/issues/916)


Jasy 1.0.1
==========

- Fixed unicode issues
- Fixed HTTP status code issues (404 did not work)


Jasy 1.0
========

## New:

- New [Skeleton based on HTML5Boilerplate](https://github.com/zynga/jasy-html5-boilerplate)
- Added support for Python 3.3. Bug fixes for local variable optimizer to correctly sort dictionaries.
- Reworked Markdown/Highlighting support into new `jasy.core.Text` module and updated dependencies accordingly.
- Refined asset export logic to better handle a few rare edge cases.
- Added unit tests for `ImageInfo` and `Text` module.
- Added more unit tests for `Session` (permutations, locales, library support, etc.)

## Improvements:

- Fixed missing `jasy.test.js` package in installation package.
- Fixed Image Info API to correctly return file type, too.
- Updated requirements list to newest versions.
- Added Sphinx to "jasy doctor"
- Fixed one remaining issue with correctly supporting proxying PUT/POST requests.
- Improved encoding support in proxy server.
- Fixed issue in block optimizer with value-less returns in if-else-if constructs.

Jasy 0.8.1
==========

## New:

- Adding support for cloning sub modules (git only)
- Adding support for executing setup commands (defined in jasyproject.yaml/json - section "setup"). Allows you to run grunt, ant, etc. before letting Jasy scan the project content.
- Added support for explicit Git urls ("git+" + url) for later support of adding support for bazaar, hg, svn, etc.
- New unit tests for `jasy.core.Cache`, `jasy.core.Config`, `jasy.vcs.Repository.isUrl()`, `jasy.core.Options`, `jasy.core.Project`,
- Correctly support proxying of HTTP `body` in `POST` and `PUT` requests when using remote proxy features of integrated web server.
- Reworked travis.ci tests to test more and better and enabled for all branches on our Github account.
- Support for (alternative) string formatted commands in `jasy.core.Util.executeCommand()`. Uses `shlex` to parse string into array.
- Support for executing commands in different working directories in `jasy.core.Util.executeCommand()`. Changed signature to make `failmsg` optional: `jasy.core.Util.executeCommand(args, failmsg?, path?)`.
- Added contributing.md for GitHub contributor feature (pull requests / issue reporting)
- Added task completion timing to measure run time of each task.

## Improvements:

- Improved `jasy.vcs.Git.getBranch()` to use native `git` methods for branch detection. This now works out of sub folders as well.
- Pack assets before compressed code in `storeCompressed` in `jasy.core.OutputManager`
- Respect static field configurations for kernel as well e.g. `setField("es5", True)` is also applied to kernel classes and dependencies.
- Imporved `jasy.core.File.sha()` call to additionally support file paths - not just file objects.
- Added support for `getStaticPermutation()` in `jasy.core.Session` to result an permutation object which only contains fields without detection configuration (aka static fields). This is used for building the kernel now.
- Fixed path to project name logic to fix handling of "jquery-ui" vs. "jquery" where both resulted in "jquery" as project name.
- Fixed `jasy.core.Session.permutate()` to correctly reset both, current permutation and translation after the loop ended.
- Improved error handling when manually defined items does not exist. Now prints out the exact item which is wrong and not the whole list.
- Fixed separate unit tests to better run standalone
- Added debugging code to permutation patcher. The detailed modifications are now visible in the log file or using the verbose mode.
- Removed useless `defaults` parameter in `jasy.core.Options`
- Moved JavaScript related unit tests into `jasy.test.js`.
- Added more related and skeleton links to `readme.md`.
- Using Zynga's fork of PIL for better safety in `requirements.txt`
- Adding `sphinx` to optional dependencies.


Jasy 0.8
========

- Removed unused jasy.core.Json module. Just use `json` from standard library instead.
- Improved compression features of `OutputManager`.
- Added and improved a lot of doc comments.
- Fixed a few issues for locale/translation support.
- Reduced number of public methods on `Session` to not show only internally used methods to the outside.
- Improved output/export logic for translations and assets.
- Added feature to back-hyphenate parameters on the command line help screen (e.g. parameter `originVersion` => command line argument `--origin-version`)


Jasy 0.8-beta6
==============

- Added support for generating API documentation using new script "bin/jasy-doc"
- Cleaned up references to `pkg_resources`.
- Added a lot of doc comments to the code.
- Added support for top-level skeletons
- Drastically improved stability of comment parser to better protect code blocks from further interpretation by documentation tags/params etc.
- Added some new unit tests for comment parser to verify stability improvements.
- Added `Inspection` module and new built-in task `showapi` to render a list to the console of all available API.
- Fixed references to new `Item` classes when defining manual layout for projects.


Jasy 0.8-beta5
==============

Bug fix release to fix issues with creating projects from remote skeletons.


Jasy 0.8-beta4
==============

This is a major rework of tons of things in Jasy to make it compatible with typical doc generators, reduce global state and global names inside jasyscript.py and protect the jasy environment by code executed in jasyscript.py.

Unfortunatly there are quite a lot of changes inside jasyscript.py as well:

- The session is not paused/resumed automatically anymore when the web server is started. This needs to be done in the jasyscript.py manually if required.
- Changed project scanning to prefer projects nearer to sort order e.g. "core" wins over "apibrowser/core" even if placed before/behind.
- Changed `jasylibrary.py` initialization so that methods are automatically imported one project dependencies are solved (works like importing fields from the projects)
- Added support for #require with wildcards aka `core.*`.
- For more details consult the migration guide in our wiki.


Jasy 0.8-beta3
==============

## New Features

- (Re-)Added support for Localization based on industry standard CLDR data
- Updated included CLDR data from 2.0 to 2.1
- Support for gettext-based translations with full support of context hints and multi plural forms.
- Support for in-place replacement of translations to reduce overhead of translations in application code (no mapping, no method calls and placeholder inlining)
- Added support for "jasy doctor" to check environment of Jasy installation
- Added `executeCommand` method to easily call external tools from `jasyscript.py`
- Allow tasks for having dashes in parameter names e.g. `--origin-version` and translate them dynamically into camelCase variant for task parameters.
- The Jasy Webserver has got support for custom mime types (plus it automatically supports all modern mime types supported by HTML5Boilerplate)
- The Webserver now supports mirroring non-GET requests.

## Changes

- Moved `AssetManager` back to the global `session` instance. That's a move back to how this was implemented in Jasy 0.6.x. Please update your `jasyscript.py` to use `session.getAssetManager()` instead of the global `assetManager`.
- Postponed project scanning and Asset initialization to allow for dyanically added projects (like "locale" projects) and improved start time for non-producing tasks (e.g. `distclean`, `clean`, `server`)
- Reduced size of generated kernel by ~30% through split of Core library classes into Jasy specific and application specific classes (core.io.Asset => core.io.Asset + jasy.Asset, ...).
- Added `jasy.datadir` which points to Jasy internal data directory
- Moved all *item* types indexed by projects into new Python package `jasy.item`. The types `Class`, `Asset`, `Doc`, `Item` and `Translation` are now placed in the same sub folder/package.
- Using new `jasy.core.Config` API for reading and writing image sprite and animation data. This means that we support YAML for both formats now as well. Changed default export format of `SpritePacker` to YAML. Configurable via new method `setDataFormat`.
- Added preliminary support for other translations formats like `.xlf`, `.txt`, and `.properties` files of the ICU standard: http://userguide.icu-project.org/locale/localizing
- Jasy now remembers the checkout revision of the origin project during `jasy create` and stores that information into the `jasyscript.yaml` of the created project.
- Implemented translation patching as an typical "optimizer" module and moved it into "jasy.js.optimizer" package.
- Splitted JS Comments `getHtml()` method store to differ between caching highlighted and non-highlighted version.
- Support for empty classes in API Browser (will be completely dropped)
- Improved API doc generation when highlighting is disabled (also disables generation of HTML pages from code)
- Added new `inMemory` cache handling to prevent memory caching of objects which are typically modified in-place later on.
- Added new method `write()` to `jasy.core.File` for unified file writing.
- Improved compression of "+" assignments further. We now also combine strings across typical AST boundaries.
- Improved compression of numbers as keys in dictionaries. These are now always compressed without quotes saving some bytes.


Jasy 0.8-beta2
==============

Mainly fixes bugs around scaffolding and interactive configuration support. Also a lot of updates to the wiki and Jasy's documentation.

Other changes:

- Added support for destination folder for created applications.
- Changed naming of built-in internatal variables.
- Added support for a flat export of `Config` objects.
- Cleanup of old binary package support.


Jasy 0.8-beta1
==============

## New Features

### Scaffolding support

- Creating new projects from scratch. Each project is able to offer one or more skeletons.
  - These "origin" projects can be available locally or can be auto-cloned from a remote repository (*GIT* only at the moment)
- Skeletons might have placeholders which are dynamically replaced with custom values e.g. name of the project.
  - The placeholder format is defined as `$${name}` to reduce conflicts with existing templating solutions
  - File patcher can handle non UTF-8 files and supports detection of binary files
- Skeletons are able to define configuration questions to the user (`ask()`, `set()`)
  - Stores configuration values as *YAML* (`jasyscript.yaml`) or *JSON* (`jasyscript.json`).
  - Questions can be answered interactively via prompt or passed in as command line arguments (`--key value`).
  - Questions can be combined with custom logic when using a custom post-creation script (`jasycreate.py`).
  - The custom script also has user friendly methods for renaming files, creating directories etc. (via `file` object)
  - Questions support type checks (basics like `String`, `Number`, etc.)
  - Questions are able to define default values.
  - All fields can use namespace notation (namespace.key as a field name) to create a structured configuration file.

### Integrated web server

- Based on *CherryPy*
- Supports configurable custom top-level routing (i.e. route requests from: /src/target to: /destination/folder/target)
- Delivers static files from the file system
- Automatically adds *CORS* header to every response so that the *Jasy* based server could be accessed from other domains/hosts.
- Supports remapping local paths to different paths on the server
- Proxying remote URLs (avoiding cross-domain oddities)
  - Caching remote *GET* requests and deliver them locally.
  - Additional offline mode omits proxying of requests which are not available in the local cache.

### Shared tooling libraries
- Allows projects to offer tooling features to other projects (via `jasylibrary.py`)
- Using `"@share"` decorator to only share specific methods to the outside
- All shared methods from each project are namespaced under an object with the name of the project.

### Other

- Added auto-installing non-native dependencies (*Pygments*, *polib*, *requests*, *CherryPy*, *PyYAML*)
  - Kept dependencies containing native code optional (*Misaka*, *PIL*)
- Added support for *YAML* throughthrough *Jasy* for config files and others (jasyproject.yaml)
- Added nice `about` task showing version, copyright and homepage
- Added support for showing optional task arguments in *Jasy*'s help screen
- Added support for "built-in" tasks to be able to execute jasy without actually having a *Jasy* project ready to use.
- Added [Travis.ci integration](http://travis-ci.org/#!/zynga/jasy) for testing scaffolding support (and more later on).
- [WIP] Started implementation of file system watcher to allow auto rebuilding based on file system changes
  - Based on Watchdog with [custom port for Python 3](https://github.com/wpbasti/watchdog) - still broken regarding *FSEvents* on *Mac OS * unfortunately

## Improvements & Fixes

- Tasks documentation is now being implemented using doc strings on the function blocks instead of a custom string inside the `@task()` decorator.
- Improved `jasy` script to allow built-in tasks (execution outside of any *Jasy* project)
- Better error handling in `jasyscript.py` and other scripts indirectly executed by *Jasy* by setting a correct file name during `compile`for debugging.
- *Jasy* options and parameters on help screen are sorted now.
- Fixed issues with missing `pkg_resources` when installing *Python on Mac* via standard (python.org) distribution
- Moved `jasy` script and prefix handling into Task module.
- Removed dependency and usage references to msgpack (never actually used anywhere in the code)
- Correctly close all `jasycache` files even if not managed by the session when *Jasy* is closed/crashed.
- Switched over from `distutils` to `distribute` for `setup.py`.
- Install `.bat` files on *Windows* only.


## APIs/Internals

- Added optional support for hashing keys of `Cache` object transparently to reduce key sizes
- Added new `jasy.core.Config` class for transparently supporting *JSON*/*YAML* formats with correct Unicode handling
- Added new module `jasy.core.File` for simplifying typical unix like file system operations (`cp`, `mv`, `mkdir`, ...)
- Reworked `jasy.core.Project` to use new `jasy.core.Config` class instead of custom config file loading.
- Added `jasy.core.Types` for a collection of new types to work with. First added type is a `CaseInsensitiveDict` which is useful for dealing with *HTTP* headers.
- Added new utility methods to `jasy.core.Util`:
  - `debounce` (useful for debouncing method calls)
  - `getFirstSubFolder` (returns the first sub folder in the given path)
  - `massFilePatcher` (is able to patch placeholders in all files of the given directory with actual content)


Jasy 0.7.5
==========

- Added option to disable syntax highlighting in API data via `ApiWriter().write("data", highlight=True/False)`


Jasy 0.7.4
==========

- Fixed issues with correctly loading cache file on some systems
- Revamped project initialization phase to be more efficient and logical while displaying a nice dependency tree during init.
- Improved version detection and handling inside `Session`/`Project`
- Internal Repository API is now less Git specific
- Made error reporting for API errors optional on console using new "printErrors" parameter in `Writer.write()`
- Improved error message output when invalid parameters are used


Jasy 0.7.3
==========

- Improved support for deep object documentation (e.g. defining a parameter x which is a map with the keys foo and bar)
- Improved comment processing: Made the text to HTML conversion lazy so that it is not done during parsing the class, but at generating API docs. Improves initial performance.
- Improved parsing/outdenting of code comments (comments which contain actual code) to not raise warnings
- Fixed detecting size of JPEGs directly saved via Photoshop
- Fixed output to log file
- Fixed `getProjectByName` to actually use the correct active session project and not simply the first found.
- Fixed project references in "requires" which uses shell shorthands like `~` for the home directory
- Fixed dependencies so that this release should really be the first which does not require any packages being installed (fixes comment parsing where we still have used Misaka in Jasy 0.7.2)


Jasy 0.7.2
==========

- Fix some issues with unused optimizer (SWFObject compilation)
- Added machine ID to verify cache is opened on same machine as created
- Some logging output improvements
- Further improved/fixed GIT support for edge cases
- Added debug logging of detailed shell output (Git only at the moment)


Jasy 0.7.1
==========

- Performance optimizations
- Improved logging output


Jasy 0.7
========

Major
-----

- Completely revamped asset handling. See migration guide for hints on how calls in jasyscript.py need to be modified.
  - Allow modular assets - moved out of kernel.js
  - Improved internal structure of assets for better compression and faster lookup
  - Support for multi profile assets (assets from different locations, roots and with different URL layouts)
  - Support for image sprites and image animations based on configuration files
  - Added information about asset types so that one can access this information on the client via core.io.Asset APIs.
- Added support for generating image sprites from source assets
- Revamped Jasy dependencies to make all dependencies optional (through disabling features). Makes initial installation of Jasy much easier. Added requirements.txt for easy installation of optional packages.
- Added support for omitting repository updates via "--fast"/"-f" option.
- Added help screen when no tasks were given and with "-h" option.

Minor
-----

- Improved categorization of project's content into classes, assets, translations, etc.
- Improved GIT cloning/updating stability.
- Improved output during processing/parsing classes for better user feedback during long runs.
- Renamed formatting=>jsFormatting, optimization=>jsOptimization in preparation of new supported types.
- Added getSortedClasses() to Resolver to omit initializing Sorter() in jasyscript.py at all, making scripts simpler again.
- Improved some edge cases for better error handling. Throwing user friendly JasyError instead of plain Exception.
- Added new utility method getChecksum() to easily detect SHA1 checksum of files.
- Removed typically unused storeCombined() method.


Jasy 0.6.1
==========

- Added `getProjectByName()`, `getGitBranch()`, `sha1File()`, `removeFile()`
- Added possibility to post-register assets using `addFile()`
- Added support for executing Jasy from inside the project structure e.g. from "source/class".
- Improved stability in project handling and git cloning


Jasy 0.6
========

- Major simplification of `jasyscript` via revamp of environment handling
- Support for auto cloning of repositories via `git` (needs system installation)
- Support for project requirements (recursively)
- Revamped console logging (colored and structured)
- Cleanup of project processing/indexing (improved stability/flexibility)
- Support for manually defined project structures to support non-jasy 3rd party projects easily
- Support for calling remote tasks
- Support for executing jasy from a other folder than the project's root


Jasy 0.6-beta2
==============

- Support for project overrides (local project overrides project with same name of any dependency) (useful for hot fixes).


Jasy 0.6-beta1
==============

- Support for checking links, param and return types inside API docs.
- Support API docs for dotted parameters (object parameters with specific required sub keys).
- Support API doc generation for plain JavaScript statics/members (using namespace={} or namespace.prototype={})
- Supporting recursive project dependencies aka project A uses B uses C and A does not know anything about C.
- Improve support for 3rd party JavaScript libraries not matching the Jasy requirements (no jasyproject.conf or matching file layout). This will be implemented moving the configuration and a manual file layout structure into the project requiring this 3rd party library.
- Support for executing and manipulating tasks from other projects e.g. generating build version of project A from project B into a destination folder of project B.
- Added support for automatic and overrideable task prefixes.
- Performance of typical initial `build` tasks was dramatically improved by adding slots and improved deep cloning support to `Node`.


Jasy 0.5
========

- No stable release. Use 0.5-beta12 or 0.6.


Jasy 0.5-beta12
===============

- Added support for validating links inside doc strings
- Added support for validating types in params and return values
- Changed doc output format for param and return types to hold info about linkability, auto-detection, array-like, builtin, pseudo, etc.

Jasy 0.5-beta11
===============

- Added packer script for Mac OS.
- Fixed a few API doc issues.

Jasy 0.5-beta10
===============

- Worked on better API support

Jasy 0.5-beta9
==============

- Improved error handling and output
- Changed format of members/events/properties/statics to sorted arrays
- Apply sorting to uses, implements, etc.

Jasy 0.5-beta8
==============

- Improved markdown handling
- Stabilization when errors happen during API generation
- Added assets and other meta information to API data

Jasy 0.5-beta7
==============

- Added size calculation of generated files to API data
- Renamed "constructor" key in API data to "construct"
- Minor bug fixes

Jasy 0.5-beta6
==============

- Added cache versioning
- Minor bug fixes

Jasy 0.5-beta5
==============

- Added support for generating a basic search index with all statics/members/properties/events
- Added support for compressing json output
- Added support for ignoring private/internal statics/members
- Added more connections between classes: includedBy and usedBy sections.

Jasy 0.5-beta4
==============

- Added support for merging extensions into destination object (e.g. polyfills, sugar for native objects like String, etc.)
- Added support for generating jsonp output files with custom callback
- Added support for readme.md/package.md package docs

Jasy 0.5-beta3
==============

- Minor fixes

Jasy 0.5-beta2
==============

- Minor fixes for paren optimization

Jasy 0.5-beta1
==============

- Initial release with support for generating API data as JSON files
- Support for generating session based API data with class/interface linking
- Changed checksum computing to SHA1 to bring it in sync with changes in Core library
- Improved installation process with dependency handling etc.

Jasy 0.4.6
==========

- Minor bug fixes

Jasy 0.4.5
==========

- Minor bug fixes

Jasy 0.4.4
==========

- Minor bug fixes

Jasy 0.4.3
==========

- Minor bug fixes

Jasy 0.4.2
==========

- Minor bug fixes

Jasy 0.4.1
==========

- Minor bug fixes

Jasy 0.4
========

- Restructed to support real installation of Jasy into system folders using easy_install or PIP.
- Changed unit test implementation to Python native library

Jasy 0.3
========

- Initial Release
