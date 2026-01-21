# AOSentry GitHub Workflow Migration Recommendations

This document provides recommendations for enabling database migrations in the AOSentry CI/CD pipeline.

## Overview

The AOSentry `build-and-deploy.yml` workflow already has a commented placeholder for migrations (lines ~220-248). This document provides the specific implementation to uncomment and configure.

## Current State

The workflow has this placeholder:

```yaml
# - name: Run database migrations
#   env:
#     DATABASE_URL: ${{ secrets.STAGING_DATABASE_URL }}
#   run: |
#     # Add migration commands here
#     echo "TODO: Run migrations"
```

## Recommended Changes

### 1. Add GitHub Secrets

Add these secrets to the AOSentry repository:

- `STAGING_DATABASE_URL`: PostgreSQL connection URL for staging (likely the Supabase connection string)
- `PRODUCTION_DATABASE_URL`: PostgreSQL connection URL for production

### 2. Update the Migration Step

Replace the commented placeholder with:

```yaml
- name: Install devflow
  run: pip install devflow

- name: Check migration status
  env:
    DATABASE_URL: ${{ secrets.STAGING_DATABASE_URL }}
  run: |
    echo "Current migration status:"
    devflow db status --env staging --json

- name: Run database migrations
  env:
    DATABASE_URL: ${{ secrets.STAGING_DATABASE_URL }}
  run: |
    echo "Applying pending migrations..."
    devflow db migrate --env staging --ci --json
```

### 3. Add Job Dependencies

If migrations are in a separate job, update deployment dependencies:

```yaml
deploy-staging:
  needs: [build, run-migrations-staging]
```

## devflow.yml Configuration for AOSentry

Create or update `devflow.yml` in the AOSentry repository:

```yaml
version: "1"

project:
  name: aosentry

database:
  migrations:
    directory: supabase/migrations
    format: supabase  # AOSentry uses Supabase, so use CLI executor
    tracking_table: schema_migrations
    tracking_schema: supabase_migrations  # Supabase CLI uses this schema

  environments:
    local:
      url_env: DATABASE_URL
    staging:
      url_env: DATABASE_URL
    production:
      url_env: DATABASE_URL
      require_approval: true

secrets:
  provider: 1password
  vault: AOCyber
  mappings:
    - name: aosentry_database_url
      op_item: AOSentry Staging
      op_field: database_url
```

## Using Supabase CLI for Self-Hosted

Since AOSentry uses self-hosted Supabase, the devflow Supabase executor uses `--db-url` flag instead of `supabase link`:

```yaml
database:
  migrations:
    format: supabase  # Uses: supabase db push --db-url $DATABASE_URL
```

The executor automatically:
1. Runs `supabase db push --db-url <connection_string>`
2. Uses Supabase's built-in migration tracking (`supabase_migrations.schema_migrations`)
3. Handles errors and reports status

### Alternative: Supabase CLI Directly in Workflow

If you prefer to use Supabase CLI directly without devflow:

```yaml
- name: Install Supabase CLI
  run: npm install -g supabase

- name: Run migrations
  env:
    DATABASE_URL: ${{ secrets.STAGING_DATABASE_URL }}
  run: |
    cd ${{ github.workspace }}
    supabase db push --db-url "$DATABASE_URL"
```

## Complete Migration Job Example

```yaml
run-migrations-staging:
  name: Run Migrations (Staging)
  needs: [build]
  if: github.ref == 'refs/heads/main'
  runs-on: ubuntu-latest

  steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Set up Python 3.11
      uses: actions/setup-python@v5
      with:
        python-version: "3.11"

    - name: Install devflow
      run: pip install devflow

    - name: Verify database connectivity
      env:
        DATABASE_URL: ${{ secrets.STAGING_DATABASE_URL }}
      run: |
        # Quick connectivity check
        python -c "import psycopg2; psycopg2.connect('$DATABASE_URL').close(); print('Database connected')"
      continue-on-error: false

    - name: Show pending migrations
      env:
        DATABASE_URL: ${{ secrets.STAGING_DATABASE_URL }}
      run: |
        devflow db status --env staging

    - name: Apply migrations
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

## Production with Approval Gate

For production deployments:

```yaml
run-migrations-production:
  name: Run Migrations (Production)
  needs: [deploy-staging]
  if: github.event.inputs.deploy_to_production == 'true'
  runs-on: ubuntu-latest
  environment: production  # Requires manual approval

  steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.11"

    - name: Install devflow
      run: pip install devflow

    - name: Preview migrations (dry run)
      env:
        DATABASE_URL: ${{ secrets.PRODUCTION_DATABASE_URL }}
      run: |
        echo "=== PRODUCTION MIGRATION PREVIEW ==="
        devflow db migrate --env production --ci --dry-run

    - name: Apply production migrations
      env:
        DATABASE_URL: ${{ secrets.PRODUCTION_DATABASE_URL }}
      run: |
        devflow db migrate --env production --ci --json
```

## Error Handling

The workflow will fail if:
1. Database connection fails
2. Any migration fails to apply
3. devflow exits with non-zero code

On failure:
- Transaction is rolled back
- Deployment is blocked
- Error details are in workflow logs

## Security Considerations

1. **Secrets**: Database URLs are passed via GitHub Secrets, never committed
2. **Network**: Ensure GitHub Actions runners can reach the database (may need VPN or IP allowlisting)
3. **Permissions**: Use a database user with appropriate permissions for migrations
4. **Audit**: All migrations are tracked with timestamps and CI run IDs
