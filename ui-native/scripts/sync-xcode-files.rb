#!/usr/bin/env ruby
# Adds missing Swift files to the Xcode project
# Usage: ruby scripts/sync-xcode-files.rb

require 'xcodeproj'

project_path = File.join(__dir__, '..', 'DevFlow.xcodeproj')
project = Xcodeproj::Project.open(project_path)

# Get the main target
target = project.targets.find { |t| t.name == 'DevFlow' }

# Get existing file references
existing_files = target.source_build_phase.files.map { |f| f.file_ref&.path }.compact

# Find all Swift files in DevFlow directory
devflow_dir = File.join(__dir__, '..', 'DevFlow')
swift_files = Dir.glob(File.join(devflow_dir, '**', '*.swift'))

# Find the main group
main_group = project.main_group.find_subpath('DevFlow', true)

added_count = 0

swift_files.each do |file_path|
  relative_path = file_path.sub("#{devflow_dir}/", '')

  # Skip if already in project
  next if existing_files.any? { |f| f&.end_with?(File.basename(file_path)) }

  # Determine the group path
  group_path = File.dirname(relative_path)

  # Find or create the group
  current_group = main_group
  unless group_path == '.'
    group_path.split('/').each do |part|
      existing = current_group.groups.find { |g| g.name == part }
      if existing
        current_group = existing
      else
        current_group = current_group.new_group(part, part)
      end
    end
  end

  # Add file reference
  file_ref = current_group.new_file(file_path)
  target.source_build_phase.add_file_reference(file_ref)

  puts "Added: #{relative_path}"
  added_count += 1
end

if added_count > 0
  project.save
  puts "\nAdded #{added_count} files to Xcode project"
else
  puts "No new files to add"
end
