<?php

declare(strict_types=1);

namespace DoctrineMigrations;

use Doctrine\DBAL\Schema\Schema;
use Doctrine\Migrations\AbstractMigration;

/**
 * Auto-generated Migration: Please modify to your needs!
 */
final class Version20260929014555 extends AbstractMigration
{
    public function getDescription(): string
    {
        return '';
    }

    public function up(Schema $schema): void
    {
        // this up() migration is auto-generated, please modify it to your needs
        $this->addSql('CREATE TABLE employee (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, name VARCHAR(100) NOT NULL, email VARCHAR(180) NOT NULL, annual_leave_days INTEGER NOT NULL, team_id INTEGER NOT NULL, CONSTRAINT FK_5D9F75A1296CD8AE FOREIGN KEY (team_id) REFERENCES team (id) NOT DEFERRABLE INITIALLY IMMEDIATE)');
        $this->addSql('CREATE UNIQUE INDEX UNIQ_5D9F75A1E7927C74 ON employee (email)');
        $this->addSql('CREATE INDEX IDX_5D9F75A1296CD8AE ON employee (team_id)');
        $this->addSql('CREATE TABLE public_holiday (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, date DATE NOT NULL, name VARCHAR(100) NOT NULL)');
        $this->addSql('CREATE UNIQUE INDEX UNIQ_8744ED86AA9E377A ON public_holiday (date)');
        $this->addSql('CREATE TABLE team (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, name VARCHAR(100) NOT NULL, manager_id INTEGER DEFAULT NULL, CONSTRAINT FK_C4E0A61F783E3463 FOREIGN KEY (manager_id) REFERENCES employee (id) NOT DEFERRABLE INITIALLY IMMEDIATE)');
        $this->addSql('CREATE INDEX IDX_C4E0A61F783E3463 ON team (manager_id)');
    }

    public function down(Schema $schema): void
    {
        // this down() migration is auto-generated, please modify it to your needs
        $this->addSql('DROP TABLE employee');
        $this->addSql('DROP TABLE public_holiday');
        $this->addSql('DROP TABLE team');
    }
}
