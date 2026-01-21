# AOCodex GitHub Workflow Migration Recommendations

This document provides recommendations for adding database migrations to the AOCodex CI/CD pipeline.

## Overview

Currently, the AOCodex `build-and-deploy.yml` workflow deploys directly to Docker Swarm without running database migrations. This can lead to schema drift and deployment failures when code expects schema changes that haven't been applied.

## Recommended Changes

### 1. Add GitHub Secret

Add the following secret to the AOCodex repository:

- `STAGING_DATABASE_URL`: PostgreSQL connection URL for the staging database

For production, add:
- `PRODUCTION_DATABASE_URL`: PostgreSQL connection URL for production

### 2. Add Migration Job to Workflow

Add this job to `.github/workflows/build-and-deploy.yml` after the build jobs but before the deploy jobs:

```yaml
# Add after build-backend and build-frontend jobs
# Add before deploy-staging job

run-migrations-staging:
  name: Run Migrations (Staging)
  needs: [build-backend, build-frontend]
  if: (github.event_name == 'push' || github.event_name == 'workflow_dispatch') && github.ref == 'refs/heads/main'
  runs-on: ubuntu-latest

  steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.11"

    - name: Install devflow
      run: pip install devflow

    - name: Run database migrations
      env:
        DATABASE_URL: ${{ secrets.STAGING_DATABASE_URL }}
      run: |
        devflow db migrate --env staging --ci --json

    - name: Verify migration status
      env:
        DATABASE_URL: ${{ secrets.STAGING_DATABASE_URL }}
      run: |
        devflow db status --env staging --json
```

### 3. Update Deploy Job Dependencies

Modify the `deploy-staging` job to depend on migrations:

```yaml
deploy-staging:
  name: Deploy to Staging
  needs: [build-backend, build-frontend, run-migrations-staging]
  # ... rest of job
```

### 4. Production Migrations (Optional)

For production deployments with approval gates:

```yaml
run-migrations-production:
  name: Run Migrations (Production)
  needs: [deploy-staging]  # Run after staging succeeds
  if: github.event_name == 'workflow_dispatch' && github.event.inputs.deploy_to_production == 'true'
  runs-on: ubuntu-latest
  environment: production  # Requires approval

  steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.11"

    - name: Install devflow
      run: pip install devflow

    - name: Dry run migrations
      env:
        DATABASE_URL: ${{ secrets.PRODUCTION_DATABASE_URL }}
      run: |
        echo "Pending migrations:"
        devflow db migrate --env production --ci --dry-run --json

    - name: Apply migrations
      env:
        DATABASE_URL: ${{ secrets.PRODUCTION_DATABASE_URL }}
      run: |
        devflow db migrate --env production --ci --json
```

## devflow.yml Configuration

Ensure AOCodex has a `devflow.yml` with proper database configuration:

```yaml
version: "1"

project:
  name: aocodex

database:
  migrations:
    directory: supabase/migrations
    format: sql  # or 'supabase' to use Supabase CLI
    tracking_table: schema_migrations
    tracking_schema: public

  environments:
    local:
      url_env: DATABASE_URL
    staging:
      url_env: DATABASE_URL  # Set in GitHub Actions
    production:
      url_env: DATABASE_URL
      require_approval: true
```

## Using Supabase CLI Executor

If you prefer to use the Supabase CLI for migrations (which handles its own tracking):

```yaml
database:
  migrations:
    directory: supabase/migrations
    format: supabase  # Use Supabase CLI
    # Or keep format: sql and add:
    use_supabase_cli: true
```

Then update the workflow to install Supabase CLI:

```yaml
- name: Install Supabase CLI
  run: npm install -g supabase

- name: Run database migrations
  env:
    DATABASE_URL: ${{ secrets.STAGING_DATABASE_URL }}
  run: |
    devflow db migrate --env staging --ci --json
```

## Safety Features

The devflow migration system includes:

1. **Advisory Locking**: Prevents concurrent migration runs
2. **Checksum Tracking**: Detects modified migrations
3. **Rollback Recording**: Tracks migration history
4. **CI Mode**: Non-interactive execution with proper exit codes
5. **JSON Output**: Machine-parseable results for CI integration

## Rollback Strategy

If a migration fails:

1. The transaction is rolled back automatically
2. The failure is recorded in the tracking table
3. The CI job exits with code 1
4. Subsequent deployment is blocked

To manually rollback, create a new migration that reverses the changes rather than modifying the original migration.
