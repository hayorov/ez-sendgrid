# 🛋 EZ [SendGrid](https://sendgrid.com)
_Manage your SendGrid templates easy. CI/CD friendly!_

### Describe your SendGrid templates `inventory.yml` file

```yaml
---
- name: Account created
  ext_id: user/account-created
  template_id: 3c5fb172-cd02-4c49-8472-48d722cf27b0
  subject: Welcome to MyService 
  html_template: templates/account-created.html
  version_id:
  keep: 5
```

### Sprinter start

```
    => cd <templates project>
    => docker run --mount type=bind,source="$(pwd)",target=/prj \
                   hayorov/ez-sendgrid \
                   sync --inventory=/prj/inventory.yml \
                        --api_key=SG.XXX
```

### `.env` file way

    => echo "INVENTORY_FILE=./my-templates.yaml\nSENDGRID_API_KEY=SG.XXX" > .env
    => docker run ...

### Additional feature

- Run `sync` with optional --template_prefix=Foo will add a prefix to all template names
- _(inventory.yml)_ Add argument `generation: legacy` to create legacy transaction email template
- _(inventory.yml)_ Argument `active: 0` allows to upload a new version of the template and stay inactive
- _(inventory.yml)_ Define `version_id` to upgrade an existing version of the template
- _(inventory.yml)_ Define `keep` to set the maximum number of versions to keep for the template
