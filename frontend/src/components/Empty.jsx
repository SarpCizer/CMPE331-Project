import Icon from "./Icon";

export default function Empty({ icon = "leaf", title, children, headingLevel = 3 }) {
  const Heading = `h${headingLevel}`;
  return (
    <div className="empty">
      <span className="empty-icon">
        <Icon name={icon} width="30" height="30" />
      </span>
      <Heading>{title}</Heading>
      <p>{children}</p>
    </div>
  );
}
