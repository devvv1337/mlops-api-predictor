# Documentation du Projet MLOps

## Architecture du Projet

(Insérer ici un diagramme d'architecture décrivant les différents composants et leurs interactions.)

## Description des Composants

### 1. API FastAPI

- Fournit des endpoints pour la prédiction et l'obtention d'informations sur le modèle.
- Sécurisée avec JWT et stockage sécurisé des mots de passe.
- Expose des métriques pour Prometheus.

### 2. MLflow

- Utilisé pour le tracking des expériences et le versionnement des modèles.
- Le modèle est enregistré dans le Model Registry avec un nom spécifique.

### 3. DVC

- Gère le versionnement des données.
- Intégré avec un stockage distant (par exemple, S3).

### 4. Prometheus et Alertmanager

- Collecte les métriques exposées par l'API.
- Gère les alertes en cas de dépassement de seuils définis.

### 5. Grafana

- Visualise les métriques collectées par Prometheus.
- Les dashboards sont provisionnés automatiquement.

## Bonnes Pratiques MLOps

- **Séparation des Préoccupations :** Chaque composant a une responsabilité bien définie.
- **Automatisation :** Les pipelines CI/CD automatisent les tests, la construction et le déploiement.
- **Sécurité :** Les secrets sont gérés de manière sécurisée. Les mots de passe sont hachés et les tokens sont signés.
- **Scalabilité :** L'architecture peut être déployée sur des orchestrateurs de conteneurs comme Kubernetes.
- **Monitoring et Alerting :** Les métriques critiques sont surveillées, et des alertes sont envoyées en cas de problème.

## Points Restants à Réaliser

- **Déploiement sur Kubernetes :** Pour une scalabilité horizontale et une haute disponibilité.
- **Intégration Continue Plus Avancée :** Inclure des tests de charge et de performance.
- **Gestion des Secrets Plus Sécurisée :** Utiliser un gestionnaire de secrets comme HashiCorp Vault.
- **Tests Plus Complets :** Couvrir davantage de cas, y compris les tests de bout en bout.

## Difficultés Rencontrées

- **Gestion des Dépendances :** Assurer la compatibilité entre les versions des bibliothèques.
- **Sécurisation de l'API :** Implémenter une authentification robuste tout en maintenant la simplicité d'utilisation.
- **Configuration des Outils de Monitoring :** Harmoniser les configurations entre Prometheus, Alertmanager et Grafana.

---
