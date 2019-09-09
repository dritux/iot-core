// iot.hpp
#ifndef IOT_HPP_
#define IOT_HPP_

#include <string>

namespace iot {

class Iot {
public:
	explicit Iot(const std::string &name);
	std::string sayHello() const;
private:
	std::string m_name;
};

}

#endif